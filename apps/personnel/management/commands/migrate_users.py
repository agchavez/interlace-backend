"""
Comando para migrar usuarios existentes a perfiles de PersonnelProfile
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.personnel.models import PersonnelProfile, Area
from apps.maintenance.models import DistributorCenter
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Migra usuarios existentes creando perfiles de PersonnelProfile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra que se haria sin ejecutar cambios',
        )
        parser.add_argument(
            '--center',
            type=int,
            required=True,
            help='ID del centro de distribucion por defecto',
        )
        parser.add_argument(
            '--area',
            type=str,
            required=True,
            help='Codigo del area por defecto (OPERATIONS, ADMINISTRATION, PEOPLE, SECURITY, DELIVERY)',
        )
        parser.add_argument(
            '--level',
            type=str,
            default='SUPERVISOR',
            help='Nivel jerarquico por defecto (OPERATIVE, SUPERVISOR, AREA_MANAGER, CD_MANAGER)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        center_id = options['center']
        area_code = options['area']
        hierarchy_level = options['level']

        self.stdout.write('=' * 70)
        self.stdout.write('MIGRACION DE USUARIOS EXISTENTES')
        self.stdout.write('=' * 70)

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n[DRY-RUN] No se realizaran cambios\n'))

        # Obtener usuarios sin perfil
        users = User.objects.filter(personnel_profile__isnull=True).order_by('id')
        total = users.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                '\n[OK] Todos los usuarios ya tienen perfil\n'
            ))
            return

        self.stdout.write(self.style.WARNING(
            f'\n[INFO] Encontrados {total} usuarios sin perfil\n'
        ))

        # Validar configuracion
        try:
            center = DistributorCenter.objects.get(id=center_id)
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Centro: {center.name}'
            ))
        except DistributorCenter.DoesNotExist:
            raise CommandError(f'[ERROR] Centro con ID {center_id} no existe')

        try:
            area = Area.objects.get(code=area_code)
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Area: {area.get_code_display()}'
            ))
        except Area.DoesNotExist:
            raise CommandError(f'[ERROR] Area {area_code} no existe')

        valid_levels = dict(PersonnelProfile.HIERARCHY_LEVEL_CHOICES).keys()
        if hierarchy_level not in valid_levels:
            raise CommandError(f'[ERROR] Nivel invalido: {hierarchy_level}')

        self.stdout.write(self.style.SUCCESS(
            f'[OK] Nivel: {hierarchy_level}\n'
        ))

        if dry_run:
            self.stdout.write('[DRY-RUN] Se crearian estos perfiles:\n')
            for user in users:
                code = f'USR{user.id:04d}'
                self.stdout.write(f'  - {user.username} -> {code}')
            return

        # Crear perfiles
        self.stdout.write('\n[INFO] Creando perfiles...\n')
        created = 0
        errors = 0

        with transaction.atomic():
            for user in users:
                try:
                    code = f'USR{user.id:04d}'
                    PersonnelProfile.objects.create(
                        user=user,
                        employee_code=code,
                        first_name=user.first_name or 'Usuario',
                        last_name=user.last_name or f'#{user.id}',
                        email=user.email,
                        primary_distributor_center=center,
                        area=area,
                        hierarchy_level=hierarchy_level,
                        position='Importado desde usuario',
                        position_type=PersonnelProfile.ADMINISTRATIVE,
                        hire_date=date.today(),
                        contract_type='PERMANENT',
                        personal_id=f'MIGRATED-{user.id}',
                        birth_date=date(1990, 1, 1),
                        gender='O',
                        phone='+504 0000-0000',
                        address='Pendiente',
                        city='Tegucigalpa',
                        is_active=user.is_active,
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'  [OK] {user.username} -> {code}'
                    ))
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'  [ERROR] {user.username}: {str(e)}'
                    ))
                    errors += 1

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(
            f'\n[RESUMEN] Creados: {created} | Errores: {errors}\n'
        ))
        self.stdout.write(
            '\n[IMPORTANTE] Revisar y actualizar los datos:\n'
            '  - Fechas de nacimiento (placeholder: 1990-01-01)\n'
            '  - Numeros de identificacion personal\n'
            '  - Direcciones y telefonos\n'
            '  - Posiciones correctas\n'
            '  - Niveles jerarquicos correctos\n'
            '  - Supervisores inmediatos\n'
        )
