"""
Crea el PerformanceMetricType `repack_boxes_per_hour` para que las sesiones
de reempaque puedan emitir samples y aparecer en los bloques Performers.

Idempotente — se puede correr múltiples veces.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea el tipo de métrica de Reempaque (repack_boxes_per_hour)'

    def handle(self, *args, **options):
        from apps.personnel.models.performance_new import PerformanceMetricType

        defaults = {
            'name': 'Reempaque · Cajas / Hora',
            'description': 'Cajas reempacadas por hora durante una sesión de reempaque.',
            'unit': 'cajas/h',
            'is_active': True,
        }

        obj, created = PerformanceMetricType.objects.update_or_create(
            code='repack_boxes_per_hour',
            defaults=defaults,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'  [+] {obj.code} · {obj.name}'))
        else:
            self.stdout.write(f'  [=] {obj.code} · {obj.name}')

        self.stdout.write(self.style.SUCCESS('\nListo. Configurá una Meta KPI desde /maintenance/metric-types '
                                              'para que aparezca en los disparadores y bloques Performers.'))
