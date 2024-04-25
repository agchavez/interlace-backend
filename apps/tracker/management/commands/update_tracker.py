from django.core.management.base import BaseCommand
from django.db.models import Avg

from apps.maintenance.models import DistributorCenter
from apps.tracker.models import TrackerModel
# Sacar el promedio de time_invested de los tracker por CD y si es 10 minutos mayor al promedio excluir del tat

class Command(BaseCommand):
    help = 'Actualizar tracker por CD'

    def handle(self, *args, **options):
        cd = DistributorCenter.objects.all()
        for c in cd:
            trackers = TrackerModel.objects.filter(distributor_center=c, status='COMPLETE')
            average = trackers.aggregate(Avg('time_invested'))
            average = average.get('time_invested__avg')
            self.stdout.write(self.style.WARNING(f'Promedio de tiempo invertido en CD {c.name} es {average}'))
            if average is None:
                average = 0
            tracker_exclude = trackers.filter(time_invested__gt=average + 600, exclude_tat=False, status='COMPLETE')
            for t in tracker_exclude:
                # t.exclude_tat = True
                # t.save()
                self.stdout.write(self.style.SUCCESS(f'Tracker {t.id} excluido del TAT, tiempo {t.time_invested} mayor al promedio {average}'))
            # si los tiempo son menores a 30 minutos del promedio se excluyen
            tracker_exclude = trackers.filter(time_invested__lt=average - 1800, exclude_tat=False, status='COMPLETE')
            # for t in tracker_exclude:
            #     # t.exclude_tat = True
            #     # t.save()
            #     self.stdout.write(self.style.SUCCESS(f'Tracker {t.id} excluido del TAT, tiempo {t.time_invested}'))
