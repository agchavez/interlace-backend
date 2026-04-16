"""
Comando para crear y configurar grupos con permisos completos del sistema.

Grupos creados:
- Security (Seguridad): Solo validar tokens EXIT_PASS en porteria
- People (RRHH/Planilla): Acceso completo a Personal, Tokens, Usuarios
- Area Head (Jefes de Area): Acceso a Personal y Tokens
- SUPERVISOR: Ver personal y gestionar tokens de su equipo
- MANAGING: Gerentes CD - Acceso completo a su centro de distribucion
- SUPERADMIN: Acceso completo a todo el sistema

Uso: python manage.py load_group_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.user.models import DetailGroup


class Command(BaseCommand):
    help = 'Crea y configura grupos con permisos del sistema'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('CONFIGURACION DE GRUPOS Y PERMISOS DEL SISTEMA')
        self.stdout.write('=' * 70)

        # ============================================
        # GRUPO: Security (Seguridad)
        # Solo puede validar tokens EXIT_PASS en porteria
        # ============================================
        self.stdout.write('\n[1] Configurando grupo: Security (Seguridad)')

        security_group = self._get_or_create_group(
            name='Security',
            description='Seguridad - Solo validar pases de salida en porteria',
            requiered_access=True
        )

        security_permissions = {
            'tokens': [
                'view_tokenrequest',
                'can_validate_token',  # Validar EXIT_PASS
            ],
        }

        self._assign_permissions(security_group, security_permissions)
        self.stdout.write(self.style.SUCCESS('  [OK] Grupo "Security" configurado'))

        # ============================================
        # GRUPO: People (RRHH/Planilla)
        # Acceso completo a Personal, Tokens (validacion planilla), Usuarios
        # ============================================
        self.stdout.write('\n[2] Configurando grupo: People (RRHH/Planilla)')

        people_group = self._get_or_create_group(
            name='People',
            description='RRHH/Planilla - Gestion de personal, tokens y usuarios',
            requiered_access=True
        )

        people_permissions = {
            # Personal - acceso completo
            'personnel': [
                'view_personnelprofile',
                'add_personnelprofile',
                'change_personnelprofile',
                'delete_personnelprofile',
                'view_area',
                'add_area',
                'change_area',
                'view_position',
                'add_position',
                'change_position',
                'view_certification',
                'add_certification',
                'change_certification',
                'delete_certification',
                'view_certificationtype',
                'add_certificationtype',
                'change_certificationtype',
            ],
            # Tokens - crear, ver, validar planilla
            'tokens': [
                'view_tokenrequest',
                'add_tokenrequest',
                'change_tokenrequest',
                'can_validate_payroll',  # Validar tokens de planilla
                'can_approve_level_1',
                'can_approve_level_2',
                'view_material',
                'add_material',
                'change_material',
                'delete_material',
                'view_externalperson',
                'add_externalperson',
                'change_externalperson',
                'delete_externalperson',
            ],
            # Usuarios - gestion
            'user': [
                'view_usermodel',
                'add_usermodel',
                'change_usermodel',
            ],
            # Mantenimientos
            'maintenance': [
                'view_productmodel',
                'add_productmodel',
                'change_productmodel',
                'view_distributorcenter',
            ],
        }

        self._assign_permissions(people_group, people_permissions)
        self.stdout.write(self.style.SUCCESS('  [OK] Grupo "People" configurado'))

        # ============================================
        # GRUPO: Area Head (Jefes de Area)
        # Acceso a Personal y Tokens de su area
        # ============================================
        self.stdout.write('\n[3] Configurando grupo: Area Head (Jefes de Area)')

        area_head_group = self._get_or_create_group(
            name='Area Head',
            description='Jefes de Area - Gestion de personal y tokens de su area',
            requiered_access=True
        )

        area_head_permissions = {
            # Personal - ver y modificar
            'personnel': [
                'view_personnelprofile',
                'change_personnelprofile',
                'view_area',
                'view_position',
                'view_certification',
                'add_certification',
                'change_certification',
            ],
            # Tokens - crear, ver, aprobar nivel 2
            'tokens': [
                'view_tokenrequest',
                'add_tokenrequest',
                'change_tokenrequest',
                'can_approve_level_1',
                'can_approve_level_2',
                # Materiales y personas externas para pases de salida
                'view_material',
                'add_material',
                'view_externalperson',
                'add_externalperson',
            ],
        }

        self._assign_permissions(area_head_group, area_head_permissions)
        self.stdout.write(self.style.SUCCESS('  [OK] Grupo "Area Head" configurado'))

        # ============================================
        # GRUPO: SUPERVISOR
        # Acceso basico a Personal y Tokens
        # ============================================
        self.stdout.write('\n[4] Configurando grupo: SUPERVISOR')

        supervisor_group = self._get_or_create_group(
            name='SUPERVISOR',
            description='Supervisores - Ver personal y gestionar tokens de su equipo',
            requiered_access=True
        )

        supervisor_permissions = {
            'personnel': [
                'view_personnelprofile',
                'view_area',
                'view_position',
            ],
            'tokens': [
                'view_tokenrequest',
                'add_tokenrequest',
                'can_approve_level_1',
                # Materiales y personas externas para pases de salida
                'view_material',
                'add_material',
                'view_externalperson',
                'add_externalperson',
            ],
        }

        self._assign_permissions(supervisor_group, supervisor_permissions)
        self.stdout.write(self.style.SUCCESS('  [OK] Grupo "SUPERVISOR" configurado'))

        # ============================================
        # GRUPO: MANAGING (Gerentes CD)
        # Acceso completo a su centro de distribucion
        # ============================================
        self.stdout.write('\n[5] Configurando grupo: MANAGING (Gerentes CD)')

        managing_group = self._get_or_create_group(
            name='MANAGING',
            description='Gerentes CD - Acceso completo a su centro de distribucion',
            requiered_access=True
        )

        managing_permissions = {
            'personnel': [
                'view_personnelprofile',
                'add_personnelprofile',
                'change_personnelprofile',
                'view_area',
                'view_position',
                'view_certification',
                'add_certification',
                'change_certification',
            ],
            'tokens': [
                'view_tokenrequest',
                'add_tokenrequest',
                'change_tokenrequest',
                'can_approve_level_1',
                'can_approve_level_2',
                'can_approve_level_3',
                # Materiales y personas externas para pases de salida
                'view_material',
                'add_material',
                'view_externalperson',
                'add_externalperson',
            ],
            'maintenance': [
                'view_distributorcenter',
            ],
            # Ciclo del Camion - acceso completo operativo
            'truck_cycle': [
                'view_pautamodel',
                'add_pautamodel',
                'change_pautamodel',
                'delete_pautamodel',
                'add_palletcomplexuploadmodel',
                'view_palletcomplexuploadmodel',
                'view_truckmodel',
                'add_truckmodel',
                'change_truckmodel',
                'view_baymodel',
                'add_baymodel',
                'change_baymodel',
                'view_productcatalogmodel',
                'add_productcatalogmodel',
                'change_productcatalogmodel',
                'view_kpitargetmodel',
                'add_kpitargetmodel',
                'change_kpitargetmodel',
                'view_inconsistencymodel',
                'add_inconsistencymodel',
                'change_inconsistencymodel',
                'delete_inconsistencymodel',
                'view_pautaphotomodel',
                'add_pautaphotomodel',
                'view_palletticketmodel',
                'add_palletticketmodel',
                'change_palletticketmodel',
                'view_pautaassignmentmodel',
                'add_pautaassignmentmodel',
                'view_pautatimestampmodel',
                'view_pautabayassignmentmodel',
                'view_checkoutvalidationmodel',
            ],
        }

        self._assign_permissions(managing_group, managing_permissions)
        self.stdout.write(self.style.SUCCESS('  [OK] Grupo "MANAGING" configurado'))

        # ============================================
        # GRUPO: SUPERADMIN (Acceso completo a todo)
        # ============================================
        self.stdout.write('\n[6] Configurando grupo: SUPERADMIN')

        superadmin_group = self._get_or_create_group(
            name='SUPERADMIN',
            description='Administrador del sistema - Acceso completo',
            requiered_access=False
        )

        superadmin_permissions = {
            # Personal - acceso completo
            'personnel': [
                'view_personnelprofile',
                'add_personnelprofile',
                'change_personnelprofile',
                'delete_personnelprofile',
                'view_area',
                'add_area',
                'change_area',
                'delete_area',
                'view_position',
                'add_position',
                'change_position',
                'delete_position',
                'view_certification',
                'add_certification',
                'change_certification',
                'delete_certification',
                'view_certificationtype',
                'add_certificationtype',
                'change_certificationtype',
                'delete_certificationtype',
            ],
            # Tokens - acceso completo
            'tokens': [
                'view_tokenrequest',
                'add_tokenrequest',
                'change_tokenrequest',
                'delete_tokenrequest',
                'can_approve_level_1',
                'can_approve_level_2',
                'can_approve_level_3',
                'can_approve_token',
                'can_reject_token',
                'can_cancel_token',
                'can_validate_token',
                'can_validate_payroll',
                'can_download_pdf',
                'can_download_receipt',
                'can_print_token',
                'can_complete_delivery',
                'can_view_reports',
                'can_export_data',
                'view_material',
                'add_material',
                'change_material',
                'delete_material',
                'view_unitofmeasure',
                'add_unitofmeasure',
                'change_unitofmeasure',
                'delete_unitofmeasure',
                'view_externalperson',
                'add_externalperson',
                'change_externalperson',
                'delete_externalperson',
            ],
            # Usuarios - acceso completo
            'user': [
                'view_usermodel',
                'add_usermodel',
                'change_usermodel',
                'delete_usermodel',
            ],
            # Mantenimientos - acceso completo
            'maintenance': [
                'view_productmodel',
                'add_productmodel',
                'change_productmodel',
                'delete_productmodel',
                'view_distributorcenter',
                'add_distributorcenter',
                'change_distributorcenter',
                'delete_distributorcenter',
                'view_outputtypemodel',
                'add_outputtypemodel',
                'change_outputtypemodel',
                'delete_outputtypemodel',
            ],
            # Ciclo del Camion - acceso completo
            'truck_cycle': [
                'view_pautamodel',
                'add_pautamodel',
                'change_pautamodel',
                'delete_pautamodel',
                'add_palletcomplexuploadmodel',
                'view_palletcomplexuploadmodel',
                'change_palletcomplexuploadmodel',
                'delete_palletcomplexuploadmodel',
                'view_truckmodel',
                'add_truckmodel',
                'change_truckmodel',
                'delete_truckmodel',
                'view_baymodel',
                'add_baymodel',
                'change_baymodel',
                'delete_baymodel',
                'view_productcatalogmodel',
                'add_productcatalogmodel',
                'change_productcatalogmodel',
                'delete_productcatalogmodel',
                'view_kpitargetmodel',
                'add_kpitargetmodel',
                'change_kpitargetmodel',
                'delete_kpitargetmodel',
                'view_inconsistencymodel',
                'add_inconsistencymodel',
                'change_inconsistencymodel',
                'delete_inconsistencymodel',
                'view_pautaphotomodel',
                'add_pautaphotomodel',
                'change_pautaphotomodel',
                'delete_pautaphotomodel',
                'view_palletticketmodel',
                'add_palletticketmodel',
                'change_palletticketmodel',
                'delete_palletticketmodel',
                'view_pautaassignmentmodel',
                'add_pautaassignmentmodel',
                'change_pautaassignmentmodel',
                'delete_pautaassignmentmodel',
                'view_pautatimestampmodel',
                'add_pautatimestampmodel',
                'view_pautabayassignmentmodel',
                'add_pautabayassignmentmodel',
                'change_pautabayassignmentmodel',
                'view_checkoutvalidationmodel',
                'add_checkoutvalidationmodel',
                'change_checkoutvalidationmodel',
                'view_pautaproductdetailmodel',
                'view_pautadeliverydetailmodel',
            ],
        }

        self._assign_permissions(superadmin_group, superadmin_permissions)
        self.stdout.write(self.style.SUCCESS('  [OK] Grupo "SUPERADMIN" configurado'))

        # ============================================
        # RESUMEN
        # ============================================
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('[RESUMEN] Grupos configurados:\n')

        groups = ['Security', 'People', 'Area Head', 'SUPERVISOR', 'MANAGING', 'SUPERADMIN']
        for group_name in groups:
            try:
                group = Group.objects.get(name=group_name)
                perm_count = group.permissions.count()
                self.stdout.write(f'  - {group_name}: {perm_count} permisos')

                # Mostrar permisos por app
                apps = {}
                for perm in group.permissions.all():
                    app = perm.content_type.app_label
                    if app not in apps:
                        apps[app] = []
                    apps[app].append(perm.codename)

                for app, perms in apps.items():
                    self.stdout.write(f'      [{app}]: {", ".join(perms[:5])}{"..." if len(perms) > 5 else ""}')

            except Group.DoesNotExist:
                self.stdout.write(f'  - {group_name}: (no existe)')

        self.stdout.write(self.style.SUCCESS('\n[OK] Grupos configurados correctamente'))
        self.stdout.write('\nPara ejecutar migraciones pendientes: python manage.py migrate')

    def _get_or_create_group(self, name, description='', requiered_access=False):
        """Crea o obtiene un grupo y su DetailGroup asociado"""
        group, created = Group.objects.get_or_create(name=name)

        if created:
            self.stdout.write(self.style.WARNING(f'  [!] Grupo "{name}" creado'))
        else:
            self.stdout.write(f'  [-] Grupo "{name}" ya existe, actualizando permisos...')

        # Crear o actualizar DetailGroup
        detail, _ = DetailGroup.objects.get_or_create(group=group)
        detail.description = description
        detail.requiered_access = requiered_access
        detail.save()

        return group

    def _assign_permissions(self, group, permissions_dict):
        """
        Asigna permisos a un grupo.

        Args:
            group: Instancia del grupo
            permissions_dict: Dict con formato {'app_label': ['codename1', 'codename2']}
        """
        all_permissions = []

        for app_label, codenames in permissions_dict.items():
            for codename in codenames:
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label
                    )
                    all_permissions.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'    [!] Permiso no encontrado: {app_label}.{codename}'
                    ))
                except Permission.MultipleObjectsReturned:
                    # Si hay multiples, tomar el primero
                    perm = Permission.objects.filter(
                        codename=codename,
                        content_type__app_label=app_label
                    ).first()
                    if perm:
                        all_permissions.append(perm)

        # Limpiar permisos anteriores y asignar nuevos
        group.permissions.set(all_permissions)

        return len(all_permissions)
