from django.contrib import admin
from apps.maintenance.models.distributor_center import DistributorCenter, RouteModel, LocationModel
from apps.maintenance.models.operator import OperatorModel
from apps.maintenance.models.trailer import TransporterModel, TrailerModel
from apps.maintenance.models.product import ProductModel, OutputTypeModel
from apps.maintenance.models.driver import DriverModel
from apps.maintenance.models.period import PeriodModel
# Register your models her

admin.site.register(DistributorCenter)
admin.site.register(RouteModel)
admin.site.register(LocationModel)
admin.site.register(OperatorModel)
admin.site.register(TransporterModel)
admin.site.register(TrailerModel)
admin.site.register(ProductModel)
admin.site.register(DriverModel)
admin.site.register(OutputTypeModel)
admin.site.register(PeriodModel)


# Titulo del Panel de Administracion
admin.site.site_header = 'Administracion de la Aplicacion'
# Titulo de la pagina de Administracion
admin.site.site_title = 'Administracion de la Aplicacion'
# Titulo de la pagina de Inicio de Administracion
admin.site.index_title = 'Administracion de la Aplicacion'

# Titulo de este modulo en el Panel de Administracion




