from django.core.management.base import BaseCommand
from apps.user.models import UserModel


class Command(BaseCommand):
    help = 'Creacion de super usuario'

    def handle(self, *args, **options):
        if not UserModel.objects.filter(username='admin').exists():
            UserModel.objects.create(
                username='agchavez',
                first_name='Gabriel',
                last_name='Chavez',
                email='agchavez@unah.hn',
                is_active=True,
                is_staff=True,
                is_superuser=True,
                password='root123'
            )
            self.stdout.write(self.style.SUCCESS('Super usuario creado exitosamente'))
        else:
            self.stdout.write(self.style.SUCCESS('Super usuario ya existe'))