"""
Siembra los PerformanceMetricType que corresponden a las métricas
automáticas calculadas desde truck_cycle (pickers, contadores, chofer de
patio). Cada sample de PersonnelMetricSample se vincula a uno de estos
tipos por su `code`.
"""
from django.core.management.base import BaseCommand
from apps.personnel.models.performance_new import PerformanceMetricType


METRICS = [
    # ----------------------------- Picker -----------------------------
    {
        'code': 'picker_pallets_per_hour',
        'name': 'Pallets/HR (Picker)',
        'description': 'Fracciones armadas entre el tiempo total de picking en horas.',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'pallets/h',
        'applicable_position_types': ['PICKER', 'LOADER'],
        'display_order': 10,
    },
    {
        'code': 'picker_loads_assembled',
        'name': 'Cargas Armadas',
        'description': 'Cantidad de transportes armados en el día.',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'cargas',
        'applicable_position_types': ['PICKER', 'LOADER'],
        'display_order': 11,
    },
    {
        'code': 'picker_time_per_pauta',
        'name': 'Tiempo por Pauta (Picker)',
        'description': 'Horas transcurridas del armado de una pauta (T1 - T0).',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'min',
        'applicable_position_types': ['PICKER', 'LOADER'],
        'display_order': 12,
    },
    {
        'code': 'picker_load_error_rate',
        'name': '% Errores de Carga',
        'description': 'Cajas con error (faltante/sobrante/cruce) sobre cajas pickeadas.',
        'metric_type': PerformanceMetricType.PERCENTAGE,
        'min_value': 0,
        'max_value': 100,
        'applicable_position_types': ['PICKER', 'LOADER'],
        'display_order': 13,
    },
    # ----------------------------- Contador ---------------------------
    {
        'code': 'counter_pallets_per_hour',
        'name': 'Pallets contados/h',
        'description': 'Total pallets (completas + fracciones) entre tiempo de conteo.',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'pallets/h',
        'applicable_position_types': ['COUNTER'],
        'display_order': 20,
    },
    {
        'code': 'counter_time_per_truck',
        'name': 'Tiempo de Conteo por Camión',
        'description': 'Minutos transcurridos entre T5 y T6 por camión.',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'min',
        'applicable_position_types': ['COUNTER'],
        'display_order': 21,
    },
    {
        'code': 'counter_error_rate',
        'name': '% Errores de Conteo',
        'description': 'Cajas con error (verificadas en despacho) sobre total de cajas.',
        'metric_type': PerformanceMetricType.PERCENTAGE,
        'min_value': 0,
        'max_value': 100,
        'applicable_position_types': ['COUNTER'],
        'display_order': 22,
    },
    # --------------------------- Chofer de Patio ----------------------
    {
        'code': 'yard_time_park_to_bay',
        'name': 'Tiempo Estacionamiento → Bahía',
        'description': 'Minutos entre T1A y T1B (ingreso a bahía).',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'min',
        'applicable_position_types': ['YARD_DRIVER'],
        'display_order': 30,
    },
    {
        'code': 'yard_time_bay_to_park',
        'name': 'Tiempo Bahía → Estacionamiento',
        'description': 'Minutos entre T8A y T8B (retorno al estacionamiento).',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'min',
        'applicable_position_types': ['YARD_DRIVER'],
        'display_order': 31,
    },
    {
        'code': 'yard_time_total_move',
        'name': 'Tiempo Total de Movimiento',
        'description': 'Suma de Estac→Bahía + Bahía→Estac por camión.',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'min',
        'applicable_position_types': ['YARD_DRIVER'],
        'display_order': 32,
    },
    {
        'code': 'yard_trucks_moved',
        'name': '# Camiones movidos',
        'description': 'Cantidad de camiones movidos en el día por el chofer de patio.',
        'metric_type': PerformanceMetricType.NUMERIC,
        'unit': 'camiones',
        'applicable_position_types': ['YARD_DRIVER'],
        'display_order': 33,
    },
]


class Command(BaseCommand):
    help = 'Siembra los PerformanceMetricType de truck_cycle (picker, contador, yard driver).'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for spec in METRICS:
            defaults = {
                'name': spec['name'],
                'description': spec.get('description', ''),
                'metric_type': spec['metric_type'],
                'unit': spec.get('unit', ''),
                'min_value': spec.get('min_value'),
                'max_value': spec.get('max_value'),
                'weight': spec.get('weight', 10),
                'is_required': spec.get('is_required', False),
                'is_active': True,
                'display_order': spec['display_order'],
                'applicable_position_types': spec['applicable_position_types'],
                'help_text': spec.get('help_text', ''),
            }
            obj, is_created = PerformanceMetricType.objects.update_or_create(
                code=spec['code'],
                defaults=defaults,
            )
            if is_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] {spec["code"]}'))
            else:
                updated += 1
                self.stdout.write(f'  [=] {spec["code"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Listo — creadas: {created}, actualizadas: {updated}, total: {len(METRICS)}'
        ))
