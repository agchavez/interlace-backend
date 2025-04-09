from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.imported.model.claim import ClaimModel

class Command(BaseCommand):
    help = 'Actualizar usuarios, crear rol Claim Service User y asignar permisos'

    def handle(self, *args, **options):
        # PASO 1: Actualizar usuarios con centros de distribución
        # self.stdout.write('Actualizando usuarios con centros de distribución...')
        # users = UserModel.objects.filter(is_active=True, centro_distribucion__isnull=False)
        #
        # for user in users:
        #     if user.distributions_centers.count() == 0:
        #         user.distributions_centers.add(user.centro_distribucion)
        #         self.stdout.write(self.style.SUCCESS(f'Usuario {user.username} actualizado exitosamente'))

        # PASO 2: Crear rol de servicio de reclamaciones
        self.stdout.write('Creando rol Claim Service User...')
        claim_service_group, created = Group.objects.get_or_create(name='Claim Service User')

        if created:
            self.stdout.write(self.style.SUCCESS('Rol Claim Service User creado exitosamente'))
        else:
            self.stdout.write('El rol Claim Service User ya existe')

        # PASO 3: Asignar permisos para gestionar reclamaciones
        self.stdout.write('Configurando permisos para el rol...')

        # Obtener el tipo de contenido para ClaimModel
        content_type = ContentType.objects.get_for_model(ClaimModel)

        # Definir los permisos que necesita el rol
        permission_codenames = [
            'view_claimmodel',   # Ver reclamos
            'add_claimmodel',    # Crear reclamos
            'change_claimmodel', # Modificar reclamos
            'delete_claimmodel'  # Eliminar reclamos
        ]

        # crear permiso change_status_claimmodel
        Permission.objects.get_or_create(
            codename='change_status_claimmodel',
            name='Can change status of ClaimModel',
            content_type=content_type
        )
        permission_codenames_service_user = [
            'view_claimmodel',
            'change_claimmodel',
            'change_status_claimmodel'
        ]
        # Obtener y asignar los permisos
        for codename in permission_codenames:
            try:
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={'name': f'Can {codename.split("_")[0]} {ClaimModel._meta.verbose_name}'}
                )
                claim_service_group.permissions.add(permission)
                self.stdout.write(f'Permiso {codename} asignado correctamente')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error con permiso {codename}: {str(e)}'))

        # A los supervisores se les asigna el permiso de change_status_claimmodelLocal



        grup_supervisor = Group.objects.get(name='SUPERVISOR')
        permission, created = Permission.objects.get_or_create(
            codename='change_status_claimmodelLocal',
            content_type=content_type,
            defaults={'name': 'Can change status of ClaimModel Local'}
        )
        grup_supervisor.permissions.add(permission)
        for codename in permission_codenames_service_user:
            try:
                permission = Permission.objects.get(codename=codename, content_type=content_type)
                grup_supervisor.permissions.add(permission)
                self.stdout.write(f'Permiso {codename} asignado al grupo SUPERVISOR')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error con permiso {codename}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Permisos asignados correctamente'))

        group_ayudante_bodega = Group.objects.get(name='AYUDANTE DE BODEGA INTERNA')

        for codename in permission_codenames:
            try:
                permission = Permission.objects.get(codename=codename, content_type=content_type)
                group_ayudante_bodega.permissions.add(permission)
                self.stdout.write(f'Permiso {codename} asignado al grupo AYUDANTE DE BODEGA INTERNA')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error con permiso {codename}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Proceso completado con éxito'))


        self.stdout.write(self.style.SUCCESS('Proceso completado con éxito'))