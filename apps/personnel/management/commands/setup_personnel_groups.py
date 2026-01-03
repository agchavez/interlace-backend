"""
Comando para configurar grupos y permisos del módulo Personnel
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.personnel.models import (
    PersonnelProfile, Area, Department, EmergencyContact,
    MedicalRecord, Certification, CertificationType, PerformanceMetric
)


class Command(BaseCommand):
    help = 'Configura grupos y permisos para el modulo Personnel'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('CONFIGURACION DE GRUPOS Y PERMISOS - MODULO PERSONNEL')
        self.stdout.write('=' * 70)

        # ============================================
        # GRUPO 1: Personal RRHH / People
        # ============================================
        self.stdout.write('\n[1] Configurando grupo: Personal RRHH')

        people_group, created = Group.objects.get_or_create(name='Personal RRHH')

        people_permissions = [
            # PersonnelProfile - TODO
            'view_personnelprofile',
            'add_personnelprofile',
            'change_personnelprofile',
            'delete_personnelprofile',

            # Area
            'view_area',
            'add_area',
            'change_area',

            # Department
            'view_department',
            'add_department',
            'change_department',

            # EmergencyContact
            'view_emergencycontact',
            'add_emergencycontact',
            'change_emergencycontact',

            # MedicalRecord - TODOS (incluye confidenciales)
            'view_medicalrecord',
            'add_medicalrecord',
            'change_medicalrecord',
            'view_confidential_medical',  # Permiso especial

            # Certification - TODOS
            'view_certification',
            'add_certification',
            'change_certification',

            # CertificationType
            'view_certificationtype',
            'add_certificationtype',
            'change_certificationtype',

            # PerformanceMetric - Solo ver
            'view_performancemetric',
        ]

        self._assign_permissions(people_group, people_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Personal RRHH" configurado con {len(people_permissions)} permisos'
        ))

        # ============================================
        # GRUPO 2: Gerentes CD
        # ============================================
        self.stdout.write('\n[2] Configurando grupo: Gerentes CD')

        cd_manager_group, created = Group.objects.get_or_create(name='Gerentes CD')

        cd_manager_permissions = [
            # PersonnelProfile - Ver y editar su centro
            'view_personnelprofile',
            'change_personnelprofile',

            # EmergencyContact
            'view_emergencycontact',

            # MedicalRecord - Solo ver de su centro (no confidenciales)
            'view_medicalrecord',

            # Certification - Ver y gestionar
            'view_certification',
            'add_certification',
            'change_certification',

            # PerformanceMetric - Ver y crear
            'view_performancemetric',
            'add_performancemetric',
        ]

        self._assign_permissions(cd_manager_group, cd_manager_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Gerentes CD" configurado con {len(cd_manager_permissions)} permisos'
        ))

        # ============================================
        # GRUPO 3: Jefes de Área
        # ============================================
        self.stdout.write('\n[3] Configurando grupo: Jefes de Area')

        area_manager_group, created = Group.objects.get_or_create(name='Jefes de Area')

        area_manager_permissions = [
            # PersonnelProfile - Ver su área
            'view_personnelprofile',

            # EmergencyContact
            'view_emergencycontact',

            # Certification - Ver
            'view_certification',

            # PerformanceMetric - Ver y crear para su equipo
            'view_performancemetric',
            'add_performancemetric',
        ]

        self._assign_permissions(area_manager_group, area_manager_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Jefes de Area" configurado con {len(area_manager_permissions)} permisos'
        ))

        # ============================================
        # GRUPO 4: Supervisores
        # ============================================
        self.stdout.write('\n[4] Configurando grupo: Supervisores')

        supervisor_group, created = Group.objects.get_or_create(name='Supervisores')

        supervisor_permissions = [
            # PersonnelProfile - Solo ver su equipo
            'view_personnelprofile',

            # Certification - Solo ver
            'view_certification',

            # PerformanceMetric - Crear y ver de su equipo
            'view_performancemetric',
            'add_performancemetric',
        ]

        self._assign_permissions(supervisor_group, supervisor_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] Grupo "Supervisores" configurado con {len(supervisor_permissions)} permisos'
        ))

        # ============================================
        # RESUMEN
        # ============================================
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('[RESUMEN] Grupos configurados correctamente:\n')

        for group_name in ['Personal RRHH', 'Gerentes CD', 'Jefes de Area', 'Supervisores']:
            group = Group.objects.get(name=group_name)
            perm_count = group.permissions.count()
            self.stdout.write(f'  - {group_name}: {perm_count} permisos')

        self.stdout.write(self.style.SUCCESS(
            '\n[TIP] Ahora asigna los usuarios a sus grupos correspondientes:\n'
            '  - Django Admin: /admin/auth/user/\n'
            '  - O por codigo: user.groups.add(group)\n'
        ))

    def _assign_permissions(self, group, permission_codenames):
        """Asigna permisos al grupo"""
        permissions = []

        for codename in permission_codenames:
            try:
                # Buscar el permiso en el módulo personnel
                perm = Permission.objects.get(
                    codename=codename,
                    content_type__app_label='personnel'
                )
                permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'    [!] Permiso no encontrado: {codename}'
                ))

        # Limpiar permisos anteriores del módulo personnel
        group.permissions.remove(
            *group.permissions.filter(content_type__app_label='personnel')
        )

        # Asignar nuevos permisos
        group.permissions.add(*permissions)
