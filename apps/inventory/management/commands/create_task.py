from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from apps.inventory.tasks import apply_inventory_movements


class Command(BaseCommand):
    help = 'Comprobaciones y creaciones de registros de tareas periodicas modulo de inventario'

    def handle(self, *args, **options):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        tarea, created = PeriodicTask.objects.get_or_create(
            interval=schedule,
            name='Tarea cada minuto, aplicar movimientos de inventario',
            task='apps.inventory.tasks.apply_inventory_movements'
        )

        self.stdout.write(self.style.SUCCESS('Tarea creada: {}'.format(tarea.name)))
