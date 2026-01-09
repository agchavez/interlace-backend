"""
Comando para configurar grupos y permisos del módulo Tokens
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Configura grupos y permisos para el modulo Tokens'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('CONFIGURACION DE GRUPOS Y PERMISOS - MODULO TOKENS')
        self.stdout.write('=' * 70)

        # Definir los permisos de tokens
        token_permissions = {
            'view_tokenrequest': 'Ver tokens',
            'add_tokenrequest': 'Crear tokens',
            'change_tokenrequest': 'Modificar tokens',
            'delete_tokenrequest': 'Eliminar tokens',
        }

        # ============================================
        # GRUPO: MANAGING (permisos completos de tokens)
        # ============================================
        self.stdout.write('\n[1] Configurando grupo: MANAGING')

        managing_group, created = Group.objects.get_or_create(name='MANAGING')
        if created:
            self.stdout.write(self.style.WARNING('  [!] Grupo MANAGING creado'))

        managing_permissions = [
            'view_tokenrequest',
            'add_tokenrequest',
            'change_tokenrequest',
        ]

        count = self._assign_token_permissions(managing_group, managing_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "MANAGING" configurado con {count} permisos de tokens'
        ))

        # ============================================
        # GRUPO: Personal RRHH (permisos completos)
        # ============================================
        self.stdout.write('\n[2] Configurando grupo: Personal RRHH')

        rrhh_group, created = Group.objects.get_or_create(name='Personal RRHH')

        rrhh_permissions = [
            'view_tokenrequest',
            'add_tokenrequest',
            'change_tokenrequest',
        ]

        count = self._assign_token_permissions(rrhh_group, rrhh_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Personal RRHH" configurado con {count} permisos de tokens'
        ))

        # ============================================
        # GRUPO: Gerentes CD (todos los permisos de tokens)
        # ============================================
        self.stdout.write('\n[3] Configurando grupo: Gerentes CD')

        cd_manager_group, created = Group.objects.get_or_create(name='Gerentes CD')

        cd_manager_permissions = [
            'view_tokenrequest',
            'add_tokenrequest',
            'change_tokenrequest',
        ]

        count = self._assign_token_permissions(cd_manager_group, cd_manager_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Gerentes CD" configurado con {count} permisos de tokens'
        ))

        # ============================================
        # GRUPO: Jefes de Area (pueden aprobar nivel 2)
        # ============================================
        self.stdout.write('\n[4] Configurando grupo: Jefes de Area')

        area_manager_group, created = Group.objects.get_or_create(name='Jefes de Area')

        area_manager_permissions = [
            'view_tokenrequest',
            'add_tokenrequest',
            'change_tokenrequest',
        ]

        count = self._assign_token_permissions(area_manager_group, area_manager_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Jefes de Area" configurado con {count} permisos de tokens'
        ))

        # ============================================
        # GRUPO: Supervisores (pueden aprobar nivel 1)
        # ============================================
        self.stdout.write('\n[5] Configurando grupo: Supervisores')

        supervisor_group, created = Group.objects.get_or_create(name='Supervisores')

        supervisor_permissions = [
            'view_tokenrequest',
            'add_tokenrequest',
            'change_tokenrequest',
        ]

        count = self._assign_token_permissions(supervisor_group, supervisor_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Supervisores" configurado con {count} permisos de tokens'
        ))

        # ============================================
        # GRUPO: Seguridad (pueden validar tokens)
        # ============================================
        self.stdout.write('\n[6] Configurando grupo: Seguridad')

        security_group, created = Group.objects.get_or_create(name='Seguridad')
        if created:
            self.stdout.write(self.style.WARNING('  [!] Grupo Seguridad creado'))

        security_permissions = [
            'view_tokenrequest',  # Solo ver para validar
        ]

        count = self._assign_token_permissions(security_group, security_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Seguridad" configurado con {count} permisos de tokens'
        ))

        # ============================================
        # RESUMEN
        # ============================================
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('[RESUMEN] Grupos con permisos de tokens:\n')

        for group_name in ['MANAGING', 'Personal RRHH', 'Gerentes CD', 'Jefes de Area', 'Supervisores', 'Seguridad']:
            try:
                group = Group.objects.get(name=group_name)
                token_perms = group.permissions.filter(content_type__app_label='tokens')
                perm_count = token_perms.count()
                perm_list = ', '.join([p.codename for p in token_perms])
                self.stdout.write(f'  - {group_name}: {perm_count} permisos ({perm_list})')
            except Group.DoesNotExist:
                self.stdout.write(f'  - {group_name}: (no existe)')

        self.stdout.write(self.style.SUCCESS('\n[OK] Permisos de tokens configurados correctamente'))

    def _assign_token_permissions(self, group, permission_codenames):
        """Asigna permisos de tokens al grupo"""
        permissions = []

        for codename in permission_codenames:
            try:
                perm = Permission.objects.get(
                    codename=codename,
                    content_type__app_label='tokens'
                )
                permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'    [!] Permiso no encontrado: tokens.{codename}'
                ))

        # Agregar permisos (no eliminamos los anteriores, solo agregamos)
        group.permissions.add(*permissions)

        return len(permissions)
