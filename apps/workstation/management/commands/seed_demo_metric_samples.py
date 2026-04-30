"""
Genera datos de prueba (PersonnelMetricSample) para hoy en cada CD.

Crea 8-12 samples por hora para las últimas 8 horas, con valores realistas
alrededor del KpiTarget (un mix de zona verde, amarilla y roja). Útil para
ver el SIC/Pi y los KPIs live de las pantallas /work/* y TVs sin esperar
operación real.

Uso: python manage.py seed_demo_metric_samples
     python manage.py seed_demo_metric_samples --dc 1 --hours 6 --replace

Idempotente con --replace: borra primero los samples del día para el CD.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.maintenance.models.distributor_center import DistributorCenter
from apps.personnel.models.metric_sample import PersonnelMetricSample
from apps.personnel.models.personnel import PersonnelProfile
from apps.truck_cycle.models.catalogs import KPITargetModel


# Mapping rol del personal → códigos de métrica que aplican
POSITION_TO_METRIC_CODES = {
    'PICKER': [
        'picker_pallets_per_hour',
        'picker_loads',
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
        'yard_park_to_bay_time',
        'yard_bay_to_park_time',
        'yard_total_move_time',
    ],
}


class Command(BaseCommand):
    help = 'Genera samples de prueba para que los dashboards muestren data ≠ 0'

    def add_arguments(self, parser):
        parser.add_argument('--dc', type=int, default=None,
                            help='ID de un CD específico (sino todos los CDs).')
        parser.add_argument('--hours', type=int, default=8,
                            help='Cuántas horas hacia atrás generar (default: 8).')
        parser.add_argument('--per-hour', type=int, default=10,
                            help='Cuántos samples por hora por personal (default: 10).')
        parser.add_argument('--replace', action='store_true',
                            help='Borra los samples del día para el CD antes de generar.')

    def handle(self, *args, **options):
        dcs = (
            [DistributorCenter.objects.get(pk=options['dc'])]
            if options['dc']
            else list(DistributorCenter.objects.all())
        )
        hours = options['hours']
        per_hour = options['per_hour']
        replace = options['replace']

        op_date = timezone.localdate()
        now = timezone.localtime()

        total_created = 0
        total_skipped = 0

        for dc in dcs:
            self.stdout.write(self.style.WARNING(f'\n=== {dc.name} ==='))

            personnel_qs = PersonnelProfile.objects.filter(
                distributor_centers=dc,
                is_active=True,
                position_type__in=['PICKER', 'COUNTER', 'YARD_DRIVER'],
            )
            if not personnel_qs.exists():
                self.stdout.write('  · sin personal activo')
                continue

            # KpiTargets vigentes del CD por código
            kpi_qs = KPITargetModel.objects.filter(
                distributor_center=dc,
                metric_type__isnull=False,
                metric_type__is_active=True,
                effective_from__lte=op_date,
            ).select_related('metric_type')
            kpi_qs = kpi_qs.filter(
                models_q_effective_to_null_or_future(op_date)
            )
            target_by_code = {k.metric_type.code: k for k in kpi_qs}
            if not target_by_code:
                self.stdout.write('  · sin KpiTargets vigentes')
                continue

            if replace:
                deleted = PersonnelMetricSample.objects.filter(
                    operational_date=op_date,
                    personnel__distributor_centers=dc,
                ).delete()[0]
                self.stdout.write(f'  · borrados {deleted} samples previos')

            bulk = []
            for person in personnel_qs:
                codes = POSITION_TO_METRIC_CODES.get(person.position_type, [])
                for code in codes:
                    kpi = target_by_code.get(code)
                    if not kpi:
                        continue
                    metric = kpi.metric_type
                    target = float(kpi.target_value)
                    warning = float(kpi.warning_threshold) if kpi.warning_threshold else target * 0.85

                    for h in range(hours):
                        sample_time = now - timedelta(hours=h)
                        if sample_time.date() != op_date:
                            # No salimos del día operativo; corta y listo.
                            break
                        for _ in range(per_hour):
                            value = _realistic_value(target, warning, kpi.direction)
                            bulk.append(PersonnelMetricSample(
                                personnel=person,
                                metric_type=metric,
                                operational_date=op_date,
                                numeric_value=Decimal(str(round(value, 4))),
                                source=PersonnelMetricSample.SOURCE_AUTO,
                                context={'demo': True, 'hour_offset': h},
                            ))

            if bulk:
                created = PersonnelMetricSample.objects.bulk_create(bulk)
                total_created += len(created)
                self.stdout.write(self.style.SUCCESS(
                    f'  · {len(created)} samples generados ({personnel_qs.count()} personas, '
                    f'{len(target_by_code)} KPIs)'
                ))
            else:
                total_skipped += 1
                self.stdout.write('  · nada que generar')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(
            f'\nResumen: {total_created} samples creados · {total_skipped} CDs sin data\n'
        ))


def _realistic_value(target: float, warning: float, direction: str) -> float:
    """
    Devuelve un valor simulado distribuido para que se vean las 3 zonas:
    ~60% verde, ~30% amarillo, ~10% rojo.
    """
    r = random.random()
    if direction == 'HIGHER_IS_BETTER':
        if r < 0.60:           # verde: ≥ target
            return random.uniform(target, target * 1.15)
        elif r < 0.90:         # amarillo: entre warning y target
            return random.uniform(warning, target)
        else:                  # rojo: < warning
            return random.uniform(max(warning * 0.6, 0), warning)
    else:  # LOWER_IS_BETTER
        if r < 0.60:           # verde: ≤ target
            return random.uniform(target * 0.7, target)
        elif r < 0.90:         # amarillo: entre target y warning
            return random.uniform(target, warning)
        else:                  # rojo: > warning
            return random.uniform(warning, warning * 1.4)


def models_q_effective_to_null_or_future(op_date):
    """Helper inline para evitar otra import."""
    from django.db.models import Q
    return Q(effective_to__isnull=True) | Q(effective_to__gte=op_date)
