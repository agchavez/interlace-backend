from django.contrib import admin

from import_export import resources
from import_export.admin import ExportActionMixin
from apps.maintenance.models.distributor_center import DistributorCenter, RouteModel, LocationModel
from apps.maintenance.models.operator import OperatorModel
from apps.maintenance.models.trailer import TransporterModel, TrailerModel
from apps.maintenance.models.product import ProductModel, OutputTypeModel
from apps.maintenance.models.driver import DriverModel
from apps.maintenance.models.period import PeriodModel

# Register your models her

admin.site.register(RouteModel)
admin.site.register(LocationModel)
admin.site.register(OperatorModel)
admin.site.register(OutputTypeModel)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ['name']
    list_filter = ['brand', 'created_at']
    # ordering = ('id', 'name', 'description', 'is_active', 'created_at', 'updated_at')


class DistributorCenterResource(resources.ModelResource):
    class Meta:
        model = DistributorCenter


class DistributorCenterAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['name']
    resource_class = DistributorCenterResource


class DriverResource(resources.ModelResource):
    class Meta:
        model = DriverModel

class DriverAdmin(admin.ModelAdmin, ExportActionMixin):
    list_display = ('id', 'first_name', 'last_name', 'created_at')
    search_fields = ['first_name', 'last_name']
    list_filter = ['created_at']
    resource_class = DriverResource



class TrailerAdmin(admin.ModelAdmin):
    list_display = ('id', 'code')
    search_fields = ['code']


class TransporterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'tractor')
    search_fields = ['code', 'name']
    list_filter = ['created_at']


class PeriodResource(resources.ModelResource):
    class Meta:
        model = PeriodModel
        fields = ('id', 'label', 'initialDate', 'distributor_center__name', 'product__name')


class PeriodAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('id', 'label', 'initialDate', 'distributor_center', 'product')
    search_fields = ['label', 'initialDate', 'product']
    list_filter = ['created_at', 'label', 'distributor_center', 'initialDate', 'product']
    resource_class = PeriodResource


admin.site.register(TransporterModel, TransporterAdmin)
admin.site.register(PeriodModel, PeriodAdmin)
admin.site.register(TrailerModel, TrailerAdmin)
admin.site.register(DriverModel, DriverAdmin)
admin.site.register(ProductModel, ProductAdmin)
admin.site.register(DistributorCenter, DistributorCenterAdmin)
# Titulo del Panel de Administracion
admin.site.site_header = 'Administracion de la Aplicacion'
# Titulo de la pagina de Administracion
admin.site.site_title = 'Administracion de la Aplicacion'
# Titulo de la pagina de Inicio de Administracion
admin.site.index_title = 'Administracion de la Aplicacion'

# Titulo de este modulo en el Panel de Administracion




