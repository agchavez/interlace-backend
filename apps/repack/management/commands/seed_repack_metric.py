"""
Crea los PerformanceMetricType de Reempaque para que las sesiones
puedan emitir samples y aparecer en bloques Performers, dashboards y
configuración de KPI Targets.

Todas las métricas usan prefijo "Reempaque ·" en el nombre para
identificarlas fácilmente en selectores y reportes.

Idempotente — se puede correr múltiples veces sin duplicar.
"""
from django.core.management.base import BaseCommand


METRICS = [
    {
        'code': 'repack_boxes_per_hour',
        'name': 'Cajas / Hora',
        'description': 'Cajas reempacadas por hora durante una sesión de reempaque.',
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
        'name': 'SKUs por sesión',
        'description': 'Cantidad de productos distintos reempacados en una sesión.',
        'unit': 'SKUs',
    },
]


class Command(BaseCommand):
    help = 'Crea/actualiza los tipos de métrica de Reempaque'

    def handle(self, *args, **options):
        from apps.personnel.models.performance_new import PerformanceMetricType

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
            tag = '[+]' if was_created else '[=]'
            self.stdout.write(self.style.SUCCESS(f'  {tag} {obj.code} · {obj.name}') if was_created else f'  {tag} {obj.code} · {obj.name}')
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Listo. {created} creadas, {updated} actualizadas.'))
        self.stdout.write(
            'Para usar estos KPI: configurá Metas KPI en /maintenance/kpi-config '
            'por CD y luego elegí los códigos en el bloque Performers o SIC del workstation.'
        )
