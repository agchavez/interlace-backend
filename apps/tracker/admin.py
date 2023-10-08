from django.contrib import admin
from  apps.tracker.models import TrackerModel

# Register your models here.
class TrackerAdmin(admin.ModelAdmin):
    list_display = ('id', 'plate_number', 'input_document_number', 'output_document_number')
    search_fields = ['plate_number', 'input_document_number', 'output_document_number','id']
    list_filter = ['created_at']

admin.site.register(TrackerModel, TrackerAdmin)