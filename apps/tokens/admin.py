"""
Configuración del Admin para el módulo de tokens
"""
from django.contrib import admin
from .models import (
    TokenRequest, PermitHourDetail, PermitDayDetail, PermitDayDate,
    ExitPassDetail, ExitPassItem, UniformDeliveryDetail, UniformItem,
    SubstitutionDetail, RateChangeDetail, OvertimeDetail, ShiftChangeDetail,
    UnitOfMeasure, Material
)


# ============ INLINE ADMINS ============

class PermitHourDetailInline(admin.StackedInline):
    model = PermitHourDetail
    extra = 0
    can_delete = False


class PermitDayDetailInline(admin.StackedInline):
    model = PermitDayDetail
    extra = 0
    can_delete = False


class ExitPassDetailInline(admin.StackedInline):
    model = ExitPassDetail
    extra = 0
    can_delete = False


class UniformDeliveryDetailInline(admin.StackedInline):
    model = UniformDeliveryDetail
    extra = 0
    can_delete = False


class SubstitutionDetailInline(admin.StackedInline):
    model = SubstitutionDetail
    extra = 0
    can_delete = False


class RateChangeDetailInline(admin.StackedInline):
    model = RateChangeDetail
    extra = 0
    can_delete = False


class OvertimeDetailInline(admin.StackedInline):
    model = OvertimeDetail
    extra = 0
    can_delete = False


class ShiftChangeDetailInline(admin.StackedInline):
    model = ShiftChangeDetail
    extra = 0
    can_delete = False


class PermitDayDateInline(admin.TabularInline):
    model = PermitDayDate
    extra = 0


class ExitPassItemInline(admin.TabularInline):
    model = ExitPassItem
    extra = 0
    raw_id_fields = ['material', 'product']


class UniformItemInline(admin.TabularInline):
    model = UniformItem
    extra = 0


# ============ TOKEN REQUEST ADMIN ============

@admin.register(TokenRequest)
class TokenRequestAdmin(admin.ModelAdmin):
    list_display = [
        'display_number',
        'token_type',
        'status',
        'personnel',
        'distributor_center',
        'valid_from',
        'valid_until',
        'created_at',
    ]
    list_filter = [
        'token_type',
        'status',
        'distributor_center',
        'created_at',
    ]
    search_fields = [
        'display_number',
        'token_code',
        'personnel__first_name',
        'personnel__last_name',
        'personnel__employee_code',
    ]
    readonly_fields = [
        'token_code',
        'display_number',
        'qr_code_url',
        'approval_progress',
        'created_at',
    ]
    raw_id_fields = [
        'personnel',
        'requested_by',
        'distributor_center',
        'approved_level_1_by',
        'approved_level_2_by',
        'approved_level_3_by',
        'rejected_by',
        'validated_by',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    inlines = [
        PermitHourDetailInline,
        PermitDayDetailInline,
        ExitPassDetailInline,
        UniformDeliveryDetailInline,
        SubstitutionDetailInline,
        RateChangeDetailInline,
        OvertimeDetailInline,
        ShiftChangeDetailInline,
    ]

    fieldsets = (
        ('Identificación', {
            'fields': ('token_code', 'display_number', 'token_type', 'status')
        }),
        ('Personal', {
            'fields': ('personnel', 'requested_by', 'distributor_center')
        }),
        ('Vigencia', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('QR Code', {
            'fields': ('qr_code_url',),
            'classes': ('collapse',)
        }),
        ('Aprobaciones', {
            'fields': (
                'requires_level_1', 'requires_level_2', 'requires_level_3',
                'approved_level_1_by', 'approved_level_1_at', 'approved_level_1_notes',
                'approved_level_2_by', 'approved_level_2_at', 'approved_level_2_notes',
                'approved_level_3_by', 'approved_level_3_at', 'approved_level_3_notes',
            ),
            'classes': ('collapse',)
        }),
        ('Rechazo', {
            'fields': ('rejected_by', 'rejected_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Validación', {
            'fields': ('validated_by', 'validated_at'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('requester_notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============ CATALOG ADMINS ============

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'abbreviation']
    search_fields = ['code', 'name']
    ordering = ['name']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'unit_of_measure', 'unit_value', 'requires_return', 'category']
    list_filter = ['category', 'requires_return', 'unit_of_measure']
    search_fields = ['code', 'name']
    ordering = ['name']


# ============ TOKEN TYPE DETAIL ADMINS ============

@admin.register(PermitHourDetail)
class PermitHourDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'reason_type',
        'hours_requested',
        'exit_time',
        'expected_return_time',
        'with_pay',
    ]
    list_filter = ['reason_type', 'with_pay']
    search_fields = ['token__display_number', 'reason_detail']
    raw_id_fields = ['token']


@admin.register(PermitDayDetail)
class PermitDayDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'date_selection_type',
        'reason',
        'with_pay',
        'start_date',
        'end_date',
    ]
    list_filter = ['date_selection_type', 'reason', 'with_pay']
    search_fields = ['token__display_number', 'reason_detail']
    raw_id_fields = ['token']
    inlines = [PermitDayDateInline]


@admin.register(ExitPassDetail)
class ExitPassDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'destination',
        'vehicle_plate',
        'driver_name',
        'expected_return_date',
    ]
    search_fields = ['token__display_number', 'destination', 'vehicle_plate']
    raw_id_fields = ['token']
    inlines = [ExitPassItemInline]


@admin.register(UniformDeliveryDetail)
class UniformDeliveryDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'is_delivered',
        'delivered_at',
        'delivered_by',
        'delivery_location',
    ]
    list_filter = ['is_delivered']
    search_fields = ['token__display_number', 'delivery_location']
    raw_id_fields = ['token', 'delivered_by']
    inlines = [UniformItemInline]


@admin.register(SubstitutionDetail)
class SubstitutionDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'substituted_personnel',
        'reason',
        'start_date',
        'end_date',
        'additional_compensation',
    ]
    list_filter = ['reason', 'additional_compensation']
    search_fields = ['token__display_number', 'substituted_personnel__first_name']
    raw_id_fields = ['token', 'substituted_personnel']


@admin.register(RateChangeDetail)
class RateChangeDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'reason',
        'current_rate',
        'new_rate',
        'rate_type',
        'start_date',
        'end_date',
    ]
    list_filter = ['reason', 'rate_type']
    search_fields = ['token__display_number']
    raw_id_fields = ['token']


@admin.register(OvertimeDetail)
class OvertimeDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'overtime_type',
        'reason',
        'overtime_date',
        'start_time',
        'end_time',
        'total_hours',
        'was_completed',
    ]
    list_filter = ['overtime_type', 'reason', 'was_completed']
    search_fields = ['token__display_number', 'assigned_task']
    raw_id_fields = ['token']


@admin.register(ShiftChangeDetail)
class ShiftChangeDetailAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'reason',
        'current_shift_name',
        'new_shift_name',
        'change_date',
        'is_permanent',
        'exchange_with',
    ]
    list_filter = ['reason', 'is_permanent']
    search_fields = ['token__display_number', 'current_shift_name', 'new_shift_name']
    raw_id_fields = ['token', 'exchange_with']
