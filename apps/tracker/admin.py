from django.contrib import admin
from apps.tracker.models import TrackerModel


class TrackerAdmin(admin.ModelAdmin):
    list_display = ('id', 'plate_number', 'input_document_number', 'output_document_number', 'get_distributor_center_name')
    search_fields = ['id']
    list_filter = ['created_at', 'distributor_center', 'status', 'type']

    def get_distributor_center_name(self, obj):
        return obj.distributor_center.name

    get_distributor_center_name.short_description = 'Distributor Center Name'

admin.site.register(TrackerModel, TrackerAdmin)