"""
Genera datos de prueba (PersonnelMetricSample) para una fecha y CDs dados.

Crea N samples por hora dentro de las horas reales de los turnos activos del CD
ese día, con valores realistas alrededor del KpiTarget (mix verde/amarillo/rojo).
Útil para ver SIC/Pi y los KPIs live de las pantallas /work/* y TVs sin
operación real.

Uso:
    python manage.py seed_demo_metric_samples
    python manage.py seed_demo_metric_samples --date 2026-05-09
    python manage.py seed_demo_metric_samples --dc 1 --date 2026-05-09 --replace

Idempotente con --replace: borra los samples del día (para el CD) antes de
generar. Cubre PICKER / COUNTER / YARD_DRIVER / REPACK (WAREHOUSE_ASSISTANT
y LOADER también se consideran para repack).
"""
import random
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from apps.maintenance.models.distributor_center import DistributorCenter, DCShiftModel
from apps.personnel.models.metric_sample import PersonnelMetricSample
from apps.personnel.models.personnel import PersonnelProfile
from apps.truck_cycle.models.catalogs import KPITargetModel


HN_TZ = ZoneInfo('America/Tegucigalpa')
DAY_MAP = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

# Códigos reales que usan los endpoints /metric-samples/workstation/ y /live/.
# Mantener sincronizado con apps/personnel/views/metric_sample_views.py.
ROLE_TO_METRIC_CODES = {
    'PICKER': [
        'picker_pallets_per_hour',
        'picker_loads_assembled',
        'picker_time_per_pauta',
        'picker_load_error_rate',
    ],
    'COUNTER': [
        'counter_pallets_per_hour',
        'counter_time_per_truck',
        'counter_error_rate',
    ],
    'YARD_DRIVER': [
        'yard_trucks_moved',
        'yard_time_park_to_bay',
        'yard_time_bay_to_park',
        'yard_time_total_move',
    ],
    'REPACK': [
        'repack_boxes_per_hour',
        'repack_total_boxes_shift',
        'repack_skus_per_session',
    ],
}

# position_type → rol de métricas. REPACK opera con asistentes de almacén.
POSITION_TO_ROLE = {
    'PICKER': 'PICKER',
    'LOADER': 'PICKER',
    'COUNTER': 'COUNTER',
    'WAREHOUSE_ASSISTANT': 'COUNTER',
    'YARD_DRIVER': 'YARD_DRIVER',
}


class Command(BaseCommand):
    help = 'Genera samples de prueba realistas para los dashboards de Workstation.'

    def add_arguments(self, parser):
        parser.add_argument('--dc', type=int, default=None,
                            help='ID de un CD específico (default: todos).')
        parser.add_argument('--date', type=str, default=None,
                            help='Fecha operacional YYYY-MM-DD (default: hoy HN).')
        parser.add_argument('--per-hour', type=int, default=3,
                            help='Samples por hora por persona (default: 3).')
        parser.add_argument('--replace', action='store_true',
                            help='Borra samples previos del día/CD antes de generar.')
        parser.add_argument('--include-repack', action='store_true', default=True,
                            help='Genera samples de repack (default: true).')
        parser.add_argument('--limit', type=int, default=None,
                            help='Limita a las primeras N personas por CD (debug).')
        parser.add_argument('--verbose-progress', action='store_true', default=False,
                            help='Imprime una línea por persona procesada.')

    def handle(self, *args, **options):
        op_date = _parse_date(options['date'])

        dcs = (
            [DistributorCenter.objects.get(pk=options['dc'])]
            if options['dc']
            else list(DistributorCenter.objects.all())
        )
        per_hour = options['per_hour']
        replace = options['replace']
        include_repack = options['include_repack']

        total_created = 0

        for dc in dcs:
            self.stdout.write(self.style.WARNING(f'\n=== {dc.name} ({op_date}) ==='))

            # Rangos datetime cubiertos por algún turno activo del CD ese día.
            # Maneja turnos que cruzan medianoche (ej. TC 20:30–06:00).
            shift_slots = _resolve_shift_slots_for_date(dc.id, op_date)
            if not shift_slots:
                self.stdout.write('  · sin turnos activos ese día — se usará 06:00–18:00 por defecto')
                fallback_start = datetime.combine(op_date, dt_time(6, 0), tzinfo=HN_TZ)
                fallback_end = datetime.combine(op_date, dt_time(18, 0), tzinfo=HN_TZ)
                shift_slots = [(fallback_start, fallback_end)]
            total_minutes = sum(int((e - s).total_seconds() // 60) for s, e in shift_slots)

            # Personal del CD (truck-cycle roles + repack si aplica).
            roles_filter = list(POSITION_TO_ROLE.keys())
            personnel_qs = PersonnelProfile.objects.filter(
                distributor_centers=dc,
                is_active=True,
                position_type__in=roles_filter,
            )
            n_personnel = personnel_qs.count()
            if not n_personnel:
                self.stdout.write('  · sin personal activo')
                continue

            # KpiTargets vigentes para esa fecha.
            kpi_qs = KPITargetModel.objects.filter(
                distributor_center=dc,
                metric_type__isnull=False,
                metric_type__is_active=True,
                effective_from__lte=op_date,
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=op_date)
            ).select_related('metric_type')
            target_by_code = {k.metric_type.code: k for k in kpi_qs}
            if not target_by_code:
                self.stdout.write('  · sin KpiTargets vigentes para esa fecha')
                continue

            if replace:
                deleted = PersonnelMetricSample.objects.filter(
                    operational_date=op_date,
                    personnel__distributor_centers=dc,
                ).delete()[0]
                self.stdout.write(f'  · borrados {deleted} samples previos')

            # Acumulamos TODAS las filas en memoria y hacemos UN SOLO INSERT
            # masivo al final. Postgres `INSERT ... VALUES (...), (...), ...`
            # con `created_at` explícito es 10-100x más rápido que
            # bulk_create + bulk_update sobre B2s con latencia de red.
            rows = []  # list of tuples
            personnel_list = list(personnel_qs[:options['limit']] if options['limit'] else personnel_qs)
            self.stdout.write(f'  · preparando data para {len(personnel_list)} personas…')

            for person in personnel_list:
                role = POSITION_TO_ROLE.get(person.position_type)
                if not role:
                    continue
                role_metrics = list(ROLE_TO_METRIC_CODES[role])
                if include_repack and person.position_type in ('WAREHOUSE_ASSISTANT', 'LOADER'):
                    role_metrics = list(set(role_metrics + ROLE_TO_METRIC_CODES['REPACK']))

                for code in role_metrics:
                    kpi = target_by_code.get(code)
                    if not kpi:
                        continue
                    metric_id = kpi.metric_type_id
                    target = float(kpi.target_value)
                    warning = (
                        float(kpi.warning_threshold)
                        if kpi.warning_threshold is not None
                        else target * 0.85
                    )

                    if code in ('repack_total_boxes_shift', 'repack_skus_per_session'):
                        for s_start, s_end in shift_slots:
                            mid = s_start + (s_end - s_start) / 2
                            rows.append((
                                person.id, metric_id, op_date,
                                Decimal(str(round(_realistic_value(target, warning, kpi.direction), 4))),
                                PersonnelMetricSample.SOURCE_AUTO, mid,
                            ))
                        continue

                    n_samples = max(1, per_hour * (total_minutes // 60))
                    for sample_ts in _evenly_spread(shift_slots, n_samples):
                        rows.append((
                            person.id, metric_id, op_date,
                            Decimal(str(round(
                                _realistic_value(target, warning, kpi.direction), 4
                            ))),
                            PersonnelMetricSample.SOURCE_AUTO, sample_ts,
                        ))

            self.stdout.write(f'  · insertando {len(rows)} filas en bulk…')
            _bulk_insert_samples(rows, op_date, dc.id)
            total_created += len(rows)
            self.stdout.write(self.style.SUCCESS(
                f'  · {len(rows)} samples · {len(personnel_list)} personas · '
                f'{len(target_by_code)} KPIs · {total_minutes//60}h de turno'
            ))

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(
            f'\nResumen: {total_created} samples creados para {op_date}\n'
        ))


def _bulk_insert_samples(rows, op_date, dc_id, batch_size=500):
    """INSERT masivo en Postgres con `created_at` explícito.

    Cada fila es una tupla: (personnel_id, metric_type_id, operational_date,
    numeric_value, source, created_at). El `context` se setea a un JSON fijo
    para reducir tráfico y tiempo de serialización.

    Por qué no usar ORM:
        - `bulk_create` no permite override de `auto_now_add` → quedaba `now()`.
        - Luego hacer `UPDATE … FROM VALUES` doblaba los round-trips.
        - Con un único INSERT por batch (default 500) bajamos a ~ceil(N/500)
          round-trips contra la BD remota.
    """
    if not rows:
        return
    from django.db import connection
    import json
    table = PersonnelMetricSample._meta.db_table
    ctx_json = json.dumps({'demo': True, 'date': str(op_date), 'dc': dc_id})
    cols = '(personnel_id, metric_type_id, operational_date, numeric_value, source, context, created_at)'
    placeholder = '(%s,%s,%s,%s,%s,%s::jsonb,%s::timestamptz)'

    with connection.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            chunk = rows[i:i + batch_size]
            params = []
            for (p_id, m_id, op_d, val, src, ts) in chunk:
                params.extend([p_id, m_id, op_d, val, src, ctx_json, ts])
            sql = (
                f'INSERT INTO "{table}" {cols} VALUES '
                + ','.join([placeholder] * len(chunk))
            )
            cur.execute(sql, params)


def _parse_date(s):
    if not s:
        return timezone.localdate()
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        raise CommandError(f'Fecha inválida: {s!r}. Usar YYYY-MM-DD.')


def _resolve_shift_slots_for_date(dc_id, op_date):
    """Devuelve una lista de (start_dt, end_dt) tz-aware para cada turno activo
    del CD el día `op_date`. Maneja turnos que cruzan medianoche: el end_dt
    queda en `op_date + 1`. Esto coincide con cómo el endpoint
    `/metric-samples/*` resuelve el rango del turno y filtra por `created_at`.
    """
    dow = DAY_MAP[op_date.weekday()]
    shifts = DCShiftModel.objects.filter(
        distributor_center_id=dc_id, day_of_week=dow, is_active=True,
    )
    slots = []
    for s in shifts:
        start_dt = datetime.combine(op_date, s.start_time, tzinfo=HN_TZ)
        if s.end_time > s.start_time:
            end_dt = datetime.combine(op_date, s.end_time, tzinfo=HN_TZ)
        else:
            end_dt = datetime.combine(op_date + timedelta(days=1), s.end_time, tzinfo=HN_TZ)
        slots.append((start_dt, end_dt))
    return slots


def _evenly_spread(slots, n):
    """Genera `n` timestamps repartidos uniformemente (con jitter) sobre los
    rangos `slots`. Pondera cada slot por su duración para que turnos largos
    reciban más samples.
    """
    if n <= 0 or not slots:
        return []
    durations = [(e - s).total_seconds() for s, e in slots]
    total = sum(durations) or 1.0
    out = []
    for (s, e), dur in zip(slots, durations):
        share = max(1, int(round(n * (dur / total))))
        for i in range(share):
            # punto base equidistante + jitter ±50% del paso
            step = dur / share
            base_secs = step * (i + 0.5)
            jitter = random.uniform(-step * 0.5, step * 0.5)
            out.append(s + timedelta(seconds=base_secs + jitter))
    random.shuffle(out)
    return out


def _realistic_value(target: float, warning: float, direction: str) -> float:
    """Distribución ~60% verde, ~30% amarillo, ~10% rojo respecto al target/trigger."""
    r = random.random()
    if direction == 'HIGHER_IS_BETTER':
        if r < 0.60:
            return random.uniform(target, target * 1.15)
        elif r < 0.90:
            return random.uniform(warning, target)
        else:
            return random.uniform(max(warning * 0.6, 0), warning)
    else:
        if r < 0.60:
            return random.uniform(target * 0.7, target)
        elif r < 0.90:
            return random.uniform(target, warning)
        else:
            return random.uniform(warning, warning * 1.4)
