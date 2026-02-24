from django.core.management.base import BaseCommand
from apps.tokens.models.catalog import UnitOfMeasure


UNITS = [
    {'code': 'UND', 'name': 'Unidad',          'abbreviation': 'und'},
    {'code': 'KG',  'name': 'Kilogramo',        'abbreviation': 'kg'},
    {'code': 'GR',  'name': 'Gramo',            'abbreviation': 'gr'},
    {'code': 'LB',  'name': 'Libra',            'abbreviation': 'lb'},
    {'code': 'LT',  'name': 'Litro',            'abbreviation': 'lt'},
    {'code': 'ML',  'name': 'Mililitro',        'abbreviation': 'ml'},
    {'code': 'MT',  'name': 'Metro',            'abbreviation': 'm'},
    {'code': 'CM',  'name': 'Centímetro',       'abbreviation': 'cm'},
    {'code': 'M2',  'name': 'Metro Cuadrado',   'abbreviation': 'm²'},
    {'code': 'M3',  'name': 'Metro Cúbico',     'abbreviation': 'm³'},
    {'code': 'PAR', 'name': 'Par',              'abbreviation': 'par'},
    {'code': 'CJA', 'name': 'Caja',             'abbreviation': 'cja'},
    {'code': 'BOL', 'name': 'Bolsa',            'abbreviation': 'bol'},
    {'code': 'GAL', 'name': 'Galón',            'abbreviation': 'gal'},
    {'code': 'ROL', 'name': 'Rollo',            'abbreviation': 'rol'},
    {'code': 'JGO', 'name': 'Juego',            'abbreviation': 'jgo'},
    {'code': 'PZA', 'name': 'Pieza',            'abbreviation': 'pza'},
    {'code': 'DOC', 'name': 'Docena',           'abbreviation': 'doc'},
    {'code': 'TON', 'name': 'Tonelada',         'abbreviation': 'ton'},
    {'code': 'H',   'name': 'Hora',             'abbreviation': 'h'},
]


class Command(BaseCommand):
    help = 'Carga las unidades de medida básicas para el catálogo de tokens'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for unit_data in UNITS:
            obj, was_created = UnitOfMeasure.objects.get_or_create(
                code=unit_data['code'],
                defaults={
                    'name': unit_data['name'],
                    'abbreviation': unit_data['abbreviation'],
                }
            )
            if was_created:
                created += 1
                self.stdout.write(f"  OK {obj.code} - {obj.name}")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nListo: {created} unidades creadas, {skipped} ya existían.'
            )
        )
