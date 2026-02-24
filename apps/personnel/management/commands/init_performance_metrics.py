"""
Comando para inicializar métricas de desempeño por defecto

Este comando crea métricas estándar que se pueden asignar a diferentes tipos de posición
"""
from django.core.management.base import BaseCommand
from apps.personnel.models.performance_new import PerformanceMetricType


class Command(BaseCommand):
    help = 'Inicializa métricas de desempeño por defecto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Elimina todas las métricas existentes antes de crear las nuevas',
        )

    def handle(self, *args, **options):
        clean = options['clean']

        if clean:
            self.stdout.write(self.style.WARNING('Eliminando métricas existentes...'))
            PerformanceMetricType.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Métricas eliminadas\n'))

        self.stdout.write(self.style.WARNING('Creando métricas por defecto...\n'))

        metrics_to_create = [
            # Métricas Generales (aplican a todos)
            {
                'name': 'Productividad',
                'code': 'productivity_score',
                'description': 'Calificación general de productividad del empleado',
                'metric_type': PerformanceMetricType.RATING,
                'weight': 25,
                'is_required': True,
                'display_order': 1,
                'applicable_position_types': [],  # Aplica a todos
                'help_text': 'Evalúe la productividad general del empleado en escala de 1 a 5'
            },
            {
                'name': 'Calidad del Trabajo',
                'code': 'quality_score',
                'description': 'Calidad y precisión en la ejecución de tareas',
                'metric_type': PerformanceMetricType.RATING,
                'weight': 25,
                'is_required': True,
                'display_order': 2,
                'applicable_position_types': [],
                'help_text': 'Evalúe la calidad y precisión del trabajo realizado'
            },
            {
                'name': 'Trabajo en Equipo',
                'code': 'teamwork_score',
                'description': 'Colaboración y comunicación con compañeros',
                'metric_type': PerformanceMetricType.RATING,
                'weight': 15,
                'is_required': True,
                'display_order': 3,
                'applicable_position_types': [],
                'help_text': 'Evalúe la capacidad de trabajar en equipo y comunicación'
            },
            {
                'name': 'Puntualidad',
                'code': 'punctuality_score',
                'description': 'Cumplimiento de horarios y plazos',
                'metric_type': PerformanceMetricType.RATING,
                'weight': 15,
                'is_required': True,
                'display_order': 4,
                'applicable_position_types': [],
                'help_text': 'Evalúe el cumplimiento de horarios y plazos establecidos'
            },
            {
                'name': 'Seguridad',
                'code': 'safety_score',
                'description': 'Cumplimiento de normas de seguridad',
                'metric_type': PerformanceMetricType.RATING,
                'weight': 20,
                'is_required': True,
                'display_order': 5,
                'applicable_position_types': [],
                'help_text': 'Evalúe el cumplimiento de normas de seguridad y uso de EPP'
            },

            # Métricas para Pickers
            {
                'name': 'Pallets Movidos',
                'code': 'pallets_moved',
                'description': 'Cantidad de pallets procesados en el período',
                'metric_type': PerformanceMetricType.NUMERIC,
                'unit': 'pallets',
                'min_value': 0,
                'max_value': 10000,
                'weight': 30,
                'is_required': False,
                'display_order': 10,
                'applicable_position_types': ['PICKER'],
                'help_text': 'Ingrese la cantidad total de pallets procesados'
            },
            {
                'name': 'Tasa de Precisión',
                'code': 'accuracy_rate',
                'description': 'Porcentaje de pedidos sin errores',
                'metric_type': PerformanceMetricType.PERCENTAGE,
                'min_value': 0,
                'max_value': 100,
                'weight': 25,
                'is_required': False,
                'display_order': 11,
                'applicable_position_types': ['PICKER', 'COUNTER'],
                'help_text': 'Porcentaje de pedidos procesados sin errores (0-100)'
            },

            # Métricas para Operadores de Montacargas
            {
                'name': 'Horas de Operación',
                'code': 'operation_hours',
                'description': 'Horas totales de operación del montacargas',
                'metric_type': PerformanceMetricType.NUMERIC,
                'unit': 'horas',
                'min_value': 0,
                'max_value': 200,
                'weight': 20,
                'is_required': False,
                'display_order': 20,
                'applicable_position_types': ['OPM'],
                'help_text': 'Ingrese las horas totales de operación'
            },
            {
                'name': 'Incidentes de Seguridad',
                'code': 'safety_incidents',
                'description': 'Número de incidentes o casi-accidentes',
                'metric_type': PerformanceMetricType.NUMERIC,
                'unit': 'incidentes',
                'min_value': 0,
                'max_value': 100,
                'weight': 30,
                'is_required': False,
                'display_order': 21,
                'applicable_position_types': ['OPM', 'YARD_DRIVER', 'DELIVERY_DRIVER'],
                'help_text': 'Número de incidentes de seguridad (menor es mejor)'
            },

            # Métricas para Conductores
            {
                'name': 'Entregas Completadas',
                'code': 'deliveries_completed',
                'description': 'Número de entregas realizadas exitosamente',
                'metric_type': PerformanceMetricType.NUMERIC,
                'unit': 'entregas',
                'min_value': 0,
                'max_value': 1000,
                'weight': 30,
                'is_required': False,
                'display_order': 30,
                'applicable_position_types': ['DELIVERY_DRIVER'],
                'help_text': 'Total de entregas completadas exitosamente'
            },
            {
                'name': 'Entregas a Tiempo',
                'code': 'on_time_delivery_rate',
                'description': 'Porcentaje de entregas realizadas en el tiempo estimado',
                'metric_type': PerformanceMetricType.PERCENTAGE,
                'min_value': 0,
                'max_value': 100,
                'weight': 25,
                'is_required': False,
                'display_order': 31,
                'applicable_position_types': ['DELIVERY_DRIVER'],
                'help_text': 'Porcentaje de entregas a tiempo (0-100)'
            },

            # Métricas para Guardias de Seguridad
            {
                'name': 'Incidentes Reportados',
                'code': 'incidents_reported',
                'description': 'Número de incidentes detectados y reportados',
                'metric_type': PerformanceMetricType.NUMERIC,
                'unit': 'incidentes',
                'min_value': 0,
                'max_value': 100,
                'weight': 25,
                'is_required': False,
                'display_order': 40,
                'applicable_position_types': ['SECURITY_GUARD'],
                'help_text': 'Cantidad de incidentes detectados y reportados'
            },
            {
                'name': 'Cumplimiento de Rondas',
                'code': 'rounds_compliance',
                'description': 'Porcentaje de rondas completadas según lo programado',
                'metric_type': PerformanceMetricType.PERCENTAGE,
                'min_value': 0,
                'max_value': 100,
                'weight': 25,
                'is_required': False,
                'display_order': 41,
                'applicable_position_types': ['SECURITY_GUARD'],
                'help_text': 'Porcentaje de rondas completadas (0-100)'
            },

            # Métricas Administrativas
            {
                'name': 'Tareas Completadas',
                'code': 'tasks_completed',
                'description': 'Número de tareas o proyectos completados',
                'metric_type': PerformanceMetricType.NUMERIC,
                'unit': 'tareas',
                'min_value': 0,
                'max_value': 200,
                'weight': 25,
                'is_required': False,
                'display_order': 50,
                'applicable_position_types': ['ADMINISTRATIVE'],
                'help_text': 'Cantidad de tareas o proyectos completados'
            },
            {
                'name': 'Cumplimiento de Plazos',
                'code': 'deadline_compliance',
                'description': 'Porcentaje de tareas entregadas en plazo',
                'metric_type': PerformanceMetricType.PERCENTAGE,
                'min_value': 0,
                'max_value': 100,
                'weight': 25,
                'is_required': False,
                'display_order': 51,
                'applicable_position_types': ['ADMINISTRATIVE'],
                'help_text': 'Porcentaje de tareas completadas en plazo (0-100)'
            },
        ]

        created_count = 0
        updated_count = 0

        for metric_data in metrics_to_create:
            metric, created = PerformanceMetricType.objects.update_or_create(
                code=metric_data['code'],
                defaults=metric_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  [+] Creada: {metric.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  [*] Actualizada: {metric.name}')
                )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\nRESUMEN:'))
        self.stdout.write(f'  Métricas creadas: {created_count}')
        self.stdout.write(f'  Métricas actualizadas: {updated_count}')
        self.stdout.write(f'  Total: {created_count + updated_count}')
        self.stdout.write(self.style.SUCCESS('\n¡Métricas inicializadas correctamente!'))
