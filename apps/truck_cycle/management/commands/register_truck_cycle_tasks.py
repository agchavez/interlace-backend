"""
Registra las tareas periódicas del ciclo del camión en django-celery-beat.

Ejecución:
    python manage.py register_truck_cycle_tasks
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore


class Command(BaseCommand):
    help = 'Registra las tareas periódicas del módulo truck_cycle en django-celery-beat.'

    def handle(self, *args, **options):
        # 00:00 diario en la zona horaria del proyecto (America/Tegucigalpa).
        tz = ZoneInfo(settings.TIME_ZONE)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=tz,
        )

        task, created = PeriodicTask.objects.update_or_create(
            task='truck_cycle.close_expired_pautas',
            defaults={
                'name': 'Cerrar pautas expiradas (truck_cycle)',
                'crontab': schedule,
                'interval': None,
                'enabled': True,
                'description': (
                    'Cierra pautas con operational_date anterior a hoy que no hayan '
                    'terminado, libera bahías y registra timestamp T16_CLOSE.'
                ),
            },
        )

        label = 'creada' if created else 'actualizada'
        self.stdout.write(self.style.SUCCESS(
            f'Tarea {label}: "{task.name}" — crontab: {schedule}'
        ))
