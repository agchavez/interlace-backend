from django.contrib import admin

from .models import RepackEntry, RepackSession


@admin.register(RepackSession)
class RepackSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'personnel', 'distributor_center', 'operational_date', 'status', 'started_at', 'ended_at')
    list_filter = ('status', 'operational_date', 'distributor_center')
    search_fields = ('personnel__first_name', 'personnel__last_name', 'notes')
    raw_id_fields = ('personnel', 'distributor_center', 'started_by')


@admin.register(RepackEntry)
class RepackEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'material_code', 'box_count', 'expiration_date', 'created_at')
    search_fields = ('material_code', 'product_name')
    list_filter = ('expiration_date',)
    raw_id_fields = ('session', 'product')
