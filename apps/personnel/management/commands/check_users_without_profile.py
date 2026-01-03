"""
Comando para revisar usuarios sin perfil de PersonnelProfile
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Lista todos los usuarios que NO tienen perfil de PersonnelProfile'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('USUARIOS SIN PERFIL DE PERSONNEL'))
        self.stdout.write(self.style.WARNING('=' * 70))

        users_without_profile = User.objects.filter(
            personnel_profile__isnull=True
        ).order_by('id')

        total = users_without_profile.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                '\n[OK] Todos los usuarios tienen perfil de PersonnelProfile\n'
            ))
            return

        self.stdout.write(self.style.WARNING(
            f'\n[!] Se encontraron {total} usuario(s) sin perfil:\n'
        ))

        self.stdout.write('{:<5} {:<20} {:<30} {:<10} {:<10}'.format(
            'ID', 'Username', 'Email', 'Activo', 'Staff'
        ))
        self.stdout.write('-' * 70)

        for user in users_without_profile:
            self.stdout.write('{:<5} {:<20} {:<30} {:<10} {:<10}'.format(
                user.id,
                user.username[:20],
                user.email[:30] if user.email else 'Sin email',
                'SI' if user.is_active else 'NO',
                'SI' if user.is_staff else 'NO',
            ))

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.WARNING(
            f'\nTotal: {total} usuario(s) sin perfil\n'
        ))

        # Listar centros de distribución disponibles
        from apps.maintenance.models import DistributorCenter
        from apps.personnel.models import Area

        centers = DistributorCenter.objects.all()
        areas = Area.objects.all()

        self.stdout.write(self.style.NOTICE('\n[INFO] Centros de Distribucion disponibles:'))
        for center in centers:
            self.stdout.write(f'   - ID {center.id}: {center.name}')

        self.stdout.write(self.style.NOTICE('\n[INFO] Areas disponibles:'))
        for area in areas:
            self.stdout.write(f'   - {area.code}: {area.get_code_display()}')

        self.stdout.write(self.style.SUCCESS(
            '\n[TIP] Para migrar estos usuarios, ejecuta:\n'
            '   python manage.py migrate_existing_users --default-center <ID> --default-area <CODIGO> --dry-run\n'
        ))
