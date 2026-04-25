from datetime import date
from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


def seed_dh01_targets(apps, schema_editor):
    """Siembra los umbrales operativos para el CD La Granja (DH01).

    Idempotente: si ya existe un target vigente para (metric_type, DC) no
    se duplica.
    """
    KPITargetModel = apps.get_model('truck_cycle', 'KPITargetModel')
    PerformanceMetricType = apps.get_model('personnel', 'PerformanceMetricType')
    DistributorCenter = apps.get_model('maintenance', 'DistributorCenter')

    # DistributorCenter.name está en uppercase; el nombre típico es "DH01 - CD LA GRANJA".
    dc = (
        DistributorCenter.objects.filter(name__icontains='DH01').first()
        or DistributorCenter.objects.filter(name__icontains='LA GRANJA').first()
    )
    if not dc:
        print('  [!] CD DH01/LA GRANJA no encontrado — saltando seed de targets.')
        return

    # (metric_code, target, trigger, direction, unit)
    metrics = [
        # Picker
        ('picker_pallets_per_hour',  Decimal('9.00'),  Decimal('8.00'),  'HIGHER_IS_BETTER', 'pallets/h'),
        ('picker_loads_assembled',   Decimal('4.00'),  Decimal('2.00'),  'HIGHER_IS_BETTER', 'cargas'),
        ('picker_time_per_pauta',    Decimal('60.00'), Decimal('90.00'), 'LOWER_IS_BETTER',  'min'),
        ('picker_load_error_rate',   Decimal('3.00'),  Decimal('5.00'),  'LOWER_IS_BETTER',  '%'),
        # Contador
        ('counter_pallets_per_hour', Decimal('2.50'),  Decimal('1.50'),  'HIGHER_IS_BETTER', 'pallets/h'),
        ('counter_time_per_truck',   Decimal('20.00'), Decimal('30.00'), 'LOWER_IS_BETTER',  'min'),
        ('counter_error_rate',       Decimal('3.00'),  Decimal('5.00'),  'LOWER_IS_BETTER',  '%'),
        # Chofer de patio
        ('yard_time_park_to_bay',    Decimal('10.00'), Decimal('15.00'), 'LOWER_IS_BETTER',  'min'),
        ('yard_time_bay_to_park',    Decimal('10.00'), Decimal('15.00'), 'LOWER_IS_BETTER',  'min'),
        ('yard_time_total_move',     Decimal('20.00'), Decimal('30.00'), 'LOWER_IS_BETTER',  'min'),
        ('yard_trucks_moved',        Decimal('22.00'), Decimal('18.00'), 'HIGHER_IS_BETTER', 'camiones'),
    ]

    effective_from = date.today()
    created = 0
    skipped = 0
    missing = []

    for code, target, trigger, direction, unit in metrics:
        mt = PerformanceMetricType.objects.filter(code=code).first()
        if not mt:
            missing.append(code)
            continue

        exists = KPITargetModel.objects.filter(
            metric_type=mt,
            distributor_center=dc,
            effective_to__isnull=True,
        ).exists()
        if exists:
            skipped += 1
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

    print(f'  [seed] DH01 La Granja: creadas {created}, saltadas {skipped}.')
    if missing:
        print(f'  [!] Faltan PerformanceMetricType: {missing}. '
              f'Correr `python manage.py seed_truck_cycle_metrics` primero.')


def remove_dh01_targets(apps, schema_editor):
    """Reversión del seed: elimina los KPITargets que apuntan a metric_type."""
    KPITargetModel = apps.get_model('truck_cycle', 'KPITargetModel')
    KPITargetModel.objects.filter(metric_type__isnull=False).delete()


class Migration(migrations.Migration):
    # atomic=False: PostgreSQL no permite CREATE INDEX en la misma transacción
    # que los INSERT del seed (pending trigger events). Cada operation corre en
    # su propia transacción para evitarlo.
    atomic = False

    dependencies = [
        ('truck_cycle', '0006_yard_return_events'),
        ('personnel', '0015_personnelmetricsample'),
        ('maintenance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kpitargetmodel',
            name='kpi_type',
            field=models.CharField(
                blank=True, null=True,
                choices=[
                    ('BOXES_PER_HOUR', 'Cajas por Hora'),
                    ('COUNT_ACCURACY', 'Precisión de Conteo'),
                    ('PICKING_ERROR_RATE', 'Tasa de Error de Picking'),
                    ('LOADING_TIME', 'Tiempo de Carga'),
                    ('DISPATCH_TIME', 'Tiempo de Despacho'),
                ],
                max_length=30, verbose_name='Tipo de KPI (legacy)',
            ),
        ),
        migrations.AlterField(
            model_name='kpitargetmodel',
            name='target_value',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Meta'),
        ),
        migrations.AlterField(
            model_name='kpitargetmodel',
            name='warning_threshold',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True,
                help_text='Valor a partir del cual se marca en amarillo (antes del rojo).',
                verbose_name='Disparador',
            ),
        ),
        migrations.AlterField(
            model_name='kpitargetmodel',
            name='unit',
            field=models.CharField(blank=True, max_length=20, verbose_name='Unidad'),
        ),
        migrations.AddField(
            model_name='kpitargetmodel',
            name='metric_type',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Vincula la meta a un PerformanceMetricType (nueva modalidad).',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='kpi_targets',
                to='personnel.performancemetrictype',
                verbose_name='Tipo de métrica',
            ),
        ),
        migrations.AddField(
            model_name='kpitargetmodel',
            name='direction',
            field=models.CharField(
                choices=[
                    ('HIGHER_IS_BETTER', 'Mayor es mejor'),
                    ('LOWER_IS_BETTER', 'Menor es mejor'),
                ],
                default='HIGHER_IS_BETTER', max_length=20, verbose_name='Dirección',
            ),
        ),
        migrations.RunPython(seed_dh01_targets, remove_dh01_targets),
        migrations.AddIndex(
            model_name='kpitargetmodel',
            index=models.Index(
                fields=['metric_type', 'distributor_center', '-effective_from'],
                name='kpitarget_metric_dc_idx',
            ),
        ),
    ]
