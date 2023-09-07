from django.contrib import admin
from apps.maintenance.models.distributor_center import DistributorCenter, RouteModel, LocationModel
from apps.maintenance.models.operator import OperatorModel
from apps.maintenance.models.trailer import TransporterModel, TrailerModel
from apps.maintenance.models.product import ProductModel
from apps.maintenance.models.driver import DriverModel
# Register your models her

admin.site.register(DistributorCenter)
admin.site.register(RouteModel)
admin.site.register(LocationModel)
admin.site.register(OperatorModel)
admin.site.register(TransporterModel)
admin.site.register(TrailerModel)
admin.site.register(ProductModel)
admin.site.register(DriverModel)


