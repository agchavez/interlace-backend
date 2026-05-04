"""
Bootstrap de Reempaque: PerformanceMetricType + (opcional) KPITargetModel.

Idempotente — se puede correr múltiples veces sin duplicar.

Ejemplos:
    # Solo crear/actualizar los tipos de métrica:
    python manage.py seed_repack_metric

    # Crear también los KPI Targets en TODOS los CDs (no sobrescribe los existentes):
    python manage.py seed_repack_metric --with-targets

    # Solo en un CD específico:
    python manage.py seed_repack_metric --with-targets --dc-id 1
    python manage.py seed_repack_metric --with-targets --dc-name "LA GRANJA"

    # Sobrescribir los KPI Targets existentes con los valores default de este comando:
    python manage.py seed_repack_metric --with-targets --force
"""
from datetime import date as date_type
from decimal import Decimal

from django.core.management.base import BaseCommand


# Catálogo de métricas (PerformanceMetricType).
METRICS = [
    {
        'code': 'repack_boxes_per_hour',
        'name': 'Cajas / Hora',
        'description': 'Cajas reempacadas por hora durante una jornada de reempaque.',
        'unit': 'cajas/h',
    },
    {
        'code': 'repack_total_boxes_shift',
        'name': 'Cajas totales del turno',
        'description': 'Total acumulado de cajas reempacadas por el operario en el día operativo.',
        'unit': 'cajas',
    },
    {
        'code': 'repack_skus_per_session',
        'name': 'SKUs por jornada',
        'description': 'Cantidad de productos distintos reempacados en una jornada.',
        'unit': 'SKUs',
    },
]


# Valores default de los KPI Targets (Meta + Disparador) por code.
# Mismo patrón que seed_kpi_targets de truck_cycle.
TARGETS = [
    # (code,                     target,             trigger,            direction,           unit)
    ('repack_boxes_per_hour',    Decimal('80.00'),   Decimal('60.00'),   'HIGHER_IS_BETTER',  'cajas/h'),
    ('repack_total_boxes_shift', Decimal('400.00'),  Decimal('250.00'),  'HIGHER_IS_BETTER',  'cajas'),
    ('repack_skus_per_session',  Decimal('5.00'),    Decimal('3.00'),    'HIGHER_IS_BETTER',  'SKUs'),
]


class Command(BaseCommand):
    help = 'Crea/actualiza tipos de métrica de Reempaque y opcionalmente sus KPI Targets por CD.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-targets', action='store_true',
            help='Además de los tipos, crea los KPI Targets en los CDs (no sobrescribe vigentes a menos que se pase --force).',
        )
        parser.add_argument('--dc-id', type=int, help='ID del CD destino (con --with-targets).')
        parser.add_argument('--dc-name', type=str, help='Nombre del CD (icontains, con --with-targets).')
        parser.add_argument(
            '--force', action='store_true',
            help='Sobrescribe los KPI Targets vigentes con los valores default de este comando.',
        )

    def handle(self, *args, **opts):
        from apps.personnel.models.performance_new import PerformanceMetricType

        # ────── 1) Tipos de métrica ──────
        self.stdout.write(self.style.MIGRATE_HEADING('\n[1/2] PerformanceMetricType de Reempaque'))
        created = updated = 0
        for m in METRICS:
            obj, was_created = PerformanceMetricType.objects.update_or_create(
                code=m['code'],
                defaults={
                    'name': m['name'],
                    'description': m['description'],
                    'unit': m['unit'],
                    'is_active': True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] {obj.code} · {obj.name}'))
            else:
                updated += 1
                self.stdout.write(f'  [=] {obj.code} · {obj.name}')

        self.stdout.write(f'  → {created} creadas, {updated} actualizadas.')

        # ────── 2) KPI Targets por CD (opcional) ──────
        if not opts.get('with_targets'):
            self.stdout.write('')
            self.stdout.write(
                'Listo. Si querés crear también los KPI Targets, corré este comando con --with-targets. '
                'O configurá Metas KPI desde /maintenance/kpi-config.'
            )
            return

        self._seed_kpi_targets(opts)

    def _seed_kpi_targets(self, opts):
        from apps.maintenance.models.distributor_center import DistributorCenter
        from apps.personnel.models.performance_new import PerformanceMetricType
        from apps.truck_cycle.models.catalogs import KPITargetModel

        self.stdout.write(self.style.MIGRATE_HEADING('\n[2/2] KPI Targets de Reempaque por CD'))

        if opts.get('dc_id'):
            dcs = list(DistributorCenter.objects.filter(pk=opts['dc_id']))
        elif opts.get('dc_name'):
            dcs = list(DistributorCenter.objects.filter(name__icontains=opts['dc_name']))
        else:
            dcs = list(DistributorCenter.objects.all())

        if not dcs:
            self.stdout.write(self.style.WARNING('  No se encontraron CDs.'))
            return

        mt_by_code = {mt.code: mt for mt in PerformanceMetricType.objects.filter(is_active=True)}
        missing = [code for code, *_ in TARGETS if code not in mt_by_code]
        if missing:
            self.stdout.write(self.style.WARNING(
                f'  Faltan PerformanceMetricType: {missing}. '
                'Corré primero `python manage.py seed_repack_metric` (sin flags).'
            ))
            return

        force = bool(opts.get('force'))
        effective_from = date_type.today()
        for dc in dcs:
            self.stdout.write(self.style.MIGRATE_HEADING(f'\n  CD: {dc.name} (id={dc.id})'))
            created = updated = skipped = 0

            for code, target, trigger, direction, unit in TARGETS:
                mt = mt_by_code[code]
                existing = (
                    KPITargetModel.objects
                    .filter(metric_type=mt, distributor_center=dc, effective_to__isnull=True)
                    .order_by('-effective_from')
                    .first()
                )
                if existing and not force:
                    skipped += 1
                    self.stdout.write(f'    [=] {code} (ya existe, target={existing.target_value})')
                    continue
                if existing and force:
                    existing.target_value = target
                    existing.warning_threshold = trigger
                    existing.direction = direction
                    existing.unit = unit
                    existing.save()
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(f'    [~] {code} actualizado · meta={target} disp={trigger}'))
                    continue

                KPITargetModel.objects.create(
                    metric_type=mt,
                    distributor_center=dc,
                    target_value=target,
                    warning_threshold=trigger,
                    direction=direction,
                    unit=unit,
                    effective_from=effective_from,
                )
                created += 1
                self.stdout.write(self.style.SUCCESS(f'    [+] {code} creado · meta={target} disp={trigger}'))

            self.stdout.write(f'    → created={created}, updated={updated}, skipped={skipped}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Listo. KPI Targets de Reempaque sembrados.'))
