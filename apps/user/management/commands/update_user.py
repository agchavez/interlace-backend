from django.core.management.base import BaseCommand
from apps.user.models import UserModel

# Recorrer todos los usuarios que tienen un centro de distribución principal pero no tienen centros de distribución asociados y agregarles el centro de distribución principal como centro de distribución asociado
class Command(BaseCommand):
    help = 'Actualizar usuarios'

    def handle(self, *args, **options):
        users = UserModel.objects.filter(is_active=True, centro_distribucion__isnull=False)

        for user in users:
            if user.distributions_centers.count() == 0:
                user.distributions_centers.add(user.centro_distribucion)
                self.stdout.write(self.style.SUCCESS(f'Usuario {user.username} actualizado exitosamente'))
        self.stdout.write(self.style.SUCCESS('Usuarios actualizados exitosamente'))