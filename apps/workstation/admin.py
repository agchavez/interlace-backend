from django.contrib import admin

from .models import (
    ProhibitionCatalog,
    RiskCatalog,
    Workstation,
    WorkstationBlock,
    WorkstationDocument,
    WorkstationImage,
)


class WorkstationBlockInline(admin.TabularInline):
    model = WorkstationBlock
    extra = 0
    fields = ['type', 'grid_x', 'grid_y', 'grid_w', 'grid_h', 'is_active']


class WorkstationDocumentInline(admin.TabularInline):
    model = WorkstationDocument
    extra = 0
    readonly_fields = ['qr_token']


class WorkstationImageInline(admin.TabularInline):
    model = WorkstationImage
    extra = 0


@admin.register(Workstation)
class WorkstationAdmin(admin.ModelAdmin):
    list_display = ['distributor_center', 'role', 'name', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'distributor_center']
    search_fields = ['distributor_center__name', 'name']
    autocomplete_fields = ['distributor_center']
    inlines = [WorkstationBlockInline, WorkstationDocumentInline, WorkstationImageInline]


@admin.register(RiskCatalog)
class RiskCatalogAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'icon_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    prepopulated_fields = {'code': ('name',)}


@admin.register(ProhibitionCatalog)
class ProhibitionCatalogAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'icon_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    prepopulated_fields = {'code': ('name',)}


@admin.register(WorkstationBlock)
class WorkstationBlockAdmin(admin.ModelAdmin):
    list_display = ['workstation', 'type', 'grid_x', 'grid_y', 'grid_w', 'grid_h', 'is_active']
    list_filter = ['type', 'is_active', 'workstation__role']
    search_fields = ['workstation__distributor_center__name']
    autocomplete_fields = ['workstation']


@admin.register(WorkstationDocument)
class WorkstationDocumentAdmin(admin.ModelAdmin):
    list_display = ['workstation', 'doc_type', 'name', 'qr_token', 'is_active', 'created_at']
    list_filter = ['doc_type', 'is_active']
    search_fields = ['name', 'workstation__distributor_center__name']
    autocomplete_fields = ['workstation']
    readonly_fields = ['qr_token']


@admin.register(WorkstationImage)
class WorkstationImageAdmin(admin.ModelAdmin):
    list_display = ['workstation', 'name', 'created_at']
    search_fields = ['name', 'workstation__distributor_center__name']
    autocomplete_fields = ['workstation']
