"""
Siembra los KPITargets de truck_cycle para un (o todos) los Centros de
Distribución. Útil cuando la migración 0007 no detectó el CD por nombre.

Uso:
    python manage.py seed_kpi_targets                          # todos los CDs activos
    python manage.py seed_kpi_targets --dc-id 1                # un CD específico
    python manage.py seed_kpi_targets --dc-name "LA GRANJA"    # busca por nombre
"""
from datetime import date as date_type
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.maintenance.models.distributor_center import DistributorCenter
from apps.personnel.models.performance_new import PerformanceMetricType
from apps.truck_cycle.models.catalogs import KPITargetModel


# Mismos valores que la migración 0007 — fuente única de verdad sería ideal
# pero por ahora los duplicamos aquí (la migración no se puede re-ejecutar).
TARGETS = [
    # (code, target, trigger, direction, unit)
    ('picker_pallets_per_hour',  Decimal('9.00'),  Decimal('8.00'),  'HIGHER_IS_BETTER', 'pallets/h'),
    ('picker_loads_assembled',   Decimal('4.00'),  Decimal('2.00'),  'HIGHER_IS_BETTER', 'cargas'),
    ('picker_time_per_pauta',    Decimal('60.00'), Decimal('90.00'), 'LOWER_IS_BETTER',  'min'),
    ('picker_load_error_rate',   Decimal('3.00'),  Decimal('5.00'),  'LOWER_IS_BETTER',  '%'),
    ('counter_pallets_per_hour', Decimal('2.50'),  Decimal('1.50'),  'HIGHER_IS_BETTER', 'pallets/h'),
    ('counter_time_per_truck',   Decimal('20.00'), Decimal('30.00'), 'LOWER_IS_BETTER',  'min'),
    ('counter_error_rate',       Decimal('3.00'),  Decimal('5.00'),  'LOWER_IS_BETTER',  '%'),
    ('yard_time_park_to_bay',    Decimal('10.00'), Decimal('15.00'), 'LOWER_IS_BETTER',  'min'),
    ('yard_time_bay_to_park',    Decimal('10.00'), Decimal('15.00'), 'LOWER_IS_BETTER',  'min'),
    ('yard_time_total_move',     Decimal('20.00'), Decimal('30.00'), 'LOWER_IS_BETTER',  'min'),
    ('yard_trucks_moved',        Decimal('22.00'), Decimal('18.00'), 'HIGHER_IS_BETTER', 'camiones'),
]


class Command(BaseCommand):
    help = 'Siembra los 11 KPITargets de truck_cycle para uno o todos los CDs.'

    def add_arguments(self, parser):
        parser.add_argument('--dc-id', type=int, help='ID del CD destino.')
        parser.add_argument('--dc-name', type=str, help='Nombre del CD (icontains).')
        parser.add_argument('--force', action='store_true',
                            help='Reemplazar targets existentes con los valores default.')

    def handle(self, *args, **opts):
        # Resolver CDs destino
        if opts['dc_id']:
            dcs = list(DistributorCenter.objects.filter(pk=opts['dc_id']))
        elif opts['dc_name']:
            dcs = list(DistributorCenter.objects.filter(name__icontains=opts['dc_name']))
        else:
            dcs = list(DistributorCenter.objects.all())

        if not dcs:
            raise CommandError('No se encontraron centros de distribución que coincidan.')

        # Cachear PerformanceMetricType por code
        mt_by_code = {mt.code: mt for mt in PerformanceMetricType.objects.filter(is_active=True)}
        missing = [code for code, *_ in TARGETS if code not in mt_by_code]
        if missing:
            raise CommandError(
                f'Faltan PerformanceMetricType: {missing}. '
                f'Correr primero `python manage.py seed_truck_cycle_metrics`.'
            )

        effective_from = date_type.today()
        for dc in dcs:
            self.stdout.write(self.style.MIGRATE_HEADING(f'\nCD: {dc.name} (id={dc.id})'))
            created = updated = skipped = 0

            for code, target, trigger, direction, unit in TARGETS:
                mt = mt_by_code[code]
                existing = KPITargetModel.objects.filter(
                    metric_type=mt,
                    distributor_center=dc,
                    effective_to__isnull=True,
                ).order_by('-effective_from').first()

                if existing and not opts['force']:
                    skipped += 1
                    continue
                if existing and opts['force']:
                    existing.target_value = target
                    existing.warning_threshold = trigger
                    existing.direction = direction
                    existing.unit = unit
                    existing.save()
                    updated += 1
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

            self.stdout.write(
                f'  created={created}, updated={updated}, skipped={skipped}'
            )

        self.stdout.write(self.style.SUCCESS('\nListo.'))
