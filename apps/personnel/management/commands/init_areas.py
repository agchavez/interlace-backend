"""
Comando para inicializar las áreas básicas del sistema
"""
from django.core.management.base import BaseCommand
from apps.personnel.models import Area


class Command(BaseCommand):
    help = 'Inicializa las areas basicas del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('INICIALIZANDO AREAS DEL SISTEMA'))
        self.stdout.write(self.style.WARNING('=' * 70))

        areas_data = [
            {
                'code': Area.OPERATIONS,
                'name': 'Operaciones',
                'description': 'Area de operaciones y logistica'
            },
            {
                'code': Area.ADMINISTRATION,
                'name': 'Administracion',
                'description': 'Area administrativa'
            },
            {
                'code': Area.PEOPLE,
                'name': 'People/RRHH',
                'description': 'Area de recursos humanos y gestion de personal'
            },
            {
                'code': Area.SECURITY,
                'name': 'Seguridad',
                'description': 'Area de seguridad'
            },
            {
                'code': Area.DELIVERY,
                'name': 'Delivery/Despachos',
                'description': 'Area de entregas y despachos'
            },
        ]

        created_count = 0
        existing_count = 0

        for area_data in areas_data:
            area, created = Area.objects.get_or_create(
                code=area_data['code'],
                defaults={
                    'name': area_data['name'],
                    'description': area_data['description'],
                    'is_active': True
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  [+] Creada: {area.code} - {area.name}'
                ))
                created_count += 1
            else:
                self.stdout.write(self.style.NOTICE(
                    f'  [=] Ya existe: {area.code} - {area.name}'
                ))
                existing_count += 1

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Proceso completado:'
            f'\n  - Areas creadas: {created_count}'
            f'\n  - Areas existentes: {existing_count}'
            f'\n  - Total: {created_count + existing_count}\n'
        ))
