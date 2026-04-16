from django.contrib import admin
from apps.truck_cycle.models.catalogs import TruckModel, BayModel
from apps.truck_cycle.models.core import PautaModel, PalletComplexUploadModel


@admin.register(TruckModel)
class TruckModelAdmin(admin.ModelAdmin):
    list_display = ['code', 'plate', 'pallet_type', 'pallet_spaces', 'is_active', 'distributor_center']
    list_filter = ['is_active', 'pallet_type', 'distributor_center']
    search_fields = ['code', 'plate']


@admin.register(BayModel)
class BayModelAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'distributor_center']
    list_filter = ['is_active', 'distributor_center']
    search_fields = ['code', 'name']


@admin.register(PautaModel)
class PautaModelAdmin(admin.ModelAdmin):
    list_display = [
        'transport_number', 'trip_number', 'status', 'operational_date',
        'total_boxes', 'total_skus', 'truck', 'distributor_center',
    ]
    list_filter = ['status', 'operational_date', 'is_reload', 'distributor_center']
    search_fields = ['transport_number', 'trip_number', 'route_code']
    date_hierarchy = 'operational_date'


@admin.register(PalletComplexUploadModel)
class PalletComplexUploadModelAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'status', 'upload_date', 'row_count', 'uploaded_by', 'distributor_center']
    list_filter = ['status', 'distributor_center']
    search_fields = ['file_name']
