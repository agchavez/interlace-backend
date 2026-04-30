"""
Carga inicial de los catálogos de Riesgos y Prohibiciones del módulo Workstation.

icon_name corresponde al nombre del componente Material UI usado en el frontend
(ver TvWorkstationPickingPage.tsx para los íconos del PPT original).

Ejecutar: python manage.py seed_workstation_catalogs
Idempotente — se puede correr múltiples veces sin duplicar.
"""
from django.core.management.base import BaseCommand

from apps.workstation.models import ProhibitionCatalog, RiskCatalog

RISKS = [
    {'code': 'tropiezo',          'name': 'Tropiezo',                'icon_name': 'DirectionsRun'},
    {'code': 'cortadura',         'name': 'Cortadura',               'icon_name': 'ContentCut'},
    {'code': 'caida_mismo_nivel', 'name': 'Caída mismo nivel',       'icon_name': 'PersonOff'},
    {'code': 'explosion_botellas','name': 'Explosión de botellas',   'icon_name': 'LocalBar'},
    {'code': 'resbalon',          'name': 'Resbalón',                'icon_name': 'WaterDrop'},
    {'code': 'atropello',         'name': 'Atropello',               'icon_name': 'LocalShipping'},
]

PROHIBITIONS = [
    {'code': 'alimentos',         'name': 'Ingerir alimentos',                 'icon_name': 'Fastfood'},
    {'code': 'celular',           'name': 'Uso de dispositivos electrónicos', 'icon_name': 'PhoneIphone'},
    {'code': 'fumar',             'name': 'Fumar en áreas no autorizadas',     'icon_name': 'SmokingRooms'},
    {'code': 'joyeria',           'name': 'Uso de joyería en almacén',         'icon_name': 'Diamond'},
]


class Command(BaseCommand):
    help = 'Carga catálogos master de Riesgos y Prohibiciones para Workstation'

    def handle(self, *args, **options):
        self._seed('Riesgos', RiskCatalog, RISKS)
        self._seed('Prohibiciones', ProhibitionCatalog, PROHIBITIONS)

    def _seed(self, label, Model, rows):
        self.stdout.write(self.style.WARNING(f'\n=== {label} ==='))
        created = updated = 0
        for row in rows:
            obj, was_created = Model.objects.update_or_create(
                code=row['code'],
                defaults={'name': row['name'], 'icon_name': row['icon_name'], 'is_active': True},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] {obj.code} · {obj.name}'))
            else:
                updated += 1
                self.stdout.write(f'  [=] {obj.code} · {obj.name}')
        self.stdout.write(self.style.SUCCESS(f'  → {created} creados, {updated} actualizados\n'))
