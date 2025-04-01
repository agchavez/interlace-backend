from django.core.management.base import BaseCommand
from apps.maintenance.models import CountryModel,DistributorCenter

# Lista de paises de centro america y el caribe

countries = [
    {"name": 'Honduras', "code": 'HN', "flag": 'hn'},
    {"name": 'Guatemala', "code": 'GT', "flag": 'gt'},
    {"name": 'El Salvador', "code": 'SV', "flag": 'sv'},
    {"name": 'Nicaragua', "code": 'NI', "flag": 'ni'},
    {"name": 'Costa Rica', "code": 'CR', "flag": 'cr'},
    {"name": 'Panama', "code": 'PA', "flag": 'pa'},
    {"name": 'Cuba', "code": 'CU', "flag": 'cu'},
    {"name": 'Jamaica', "code": 'JM', "flag": 'jm'},
    {"name": 'Haiti', "code": 'HT', "flag": 'ht'},
    {"name": 'Republica Dominicana', "code": 'DO', "flag": 'do'},
    {"name": 'Puerto Rico', "code": 'PR', "flag": 'pr'},
    {"name": 'Trinidad y Tobago', "code": 'TT', "flag": 'tt'},
    {"name": 'Barbados', "code": 'BB', "flag": 'bb'},
    {"name": 'Bahamas', "code": 'BS', "flag": 'bs'},
    {"name": 'Antigua y Barbuda', "code": 'AG', "flag": 'ag'},
    {"name": 'Santa Lucia', "code": 'LC', "flag": 'lc'},
    {"name": 'San Vicente y las Granadinas', "code": 'VC', "flag": 'vc'},
    {"name": 'Grenada', "code": 'GD', "flag": 'gd'},
    {"name": 'Dominica', "code": 'DM', "flag": 'dm'},
    {"name": 'Belice', "code": 'BZ', "flag": 'bz'}
]
class Command(BaseCommand):
    help = 'Carga los datos iniciales de la aplicacion'

    def handle(self, *args, **options):

        for country in countries:
            # Verifica si el pais ya existe
            if not CountryModel.objects.filter(code=country['code']).exists():
                CountryModel.objects.create(
                    name=country['name'],
                    code=country['code'],
                    flag=country['flag']
                )

        self.stdout.write(self.style.SUCCESS('Datos cargados exitosamente'))
    # Actualizar los centros de distribucion asociados a los paises en base al codigo de pais
        for distributor_center in DistributorCenter.objects.all():
            country = CountryModel.objects.filter(code=distributor_center.country_code).first()
            if country:
                distributor_center.country = country
                distributor_center.save()
        self.stdout.write(self.style.SUCCESS('Centros de distribucion actualizados exitosamente'))

