"""
Configuración del admin para el módulo personnel
"""
from django.contrib import admin
from .models import (
    Area,
    Department,
    PersonnelProfile,
    EmergencyContact,
    MedicalRecord,
    Certification,
    CertificationType,
    PerformanceMetric,
    PerformanceMetricType,
    PerformanceEvaluation,
    EvaluationMetricValue,
)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'area', 'is_active', 'created_at']
    list_filter = ['area', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['area', 'name']


class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1
    fields = ['name', 'relationship', 'phone', 'alternate_phone', 'is_primary']


@admin.register(PersonnelProfile)
class PersonnelProfileAdmin(admin.ModelAdmin):
    list_display = [
        'employee_code',
        'full_name',
        'position',
        'hierarchy_level',
        'area',
        'primary_distributor_center',
        'is_active',
        'hire_date'
    ]
    list_filter = [
        'is_active',
        'hierarchy_level',
        'position_type',
        'area',
        'primary_distributor_center',
        'contract_type'
    ]
    search_fields = [
        'employee_code',
        'first_name',
        'last_name',
        'personal_id',
        'email',
        'phone'
    ]
    ordering = ['-is_active', 'first_name', 'last_name']
    date_hierarchy = 'hire_date'

    fieldsets = (
        ('Usuario del Sistema', {
            'fields': ('user',),
            'description': 'Usuario asociado (opcional - solo para personal con acceso a la plataforma)'
        }),
        ('Información Básica', {
            'fields': (
                'employee_code',
                'first_name',
                'last_name',
                'email',
                'photo',
                'personal_id',
                'birth_date',
                'gender',
                'marital_status'
            )
        }),
        ('Información Laboral', {
            'fields': (
                'primary_distributor_center',
                'distributor_centers',
                'area',
                'department',
                'hierarchy_level',
                'position',
                'position_type',
                'immediate_supervisor',
                'hire_date',
                'contract_type'
            )
        }),
        ('Contacto', {
            'fields': (
                'phone',
                'personal_email',
                'address',
                'city'
            )
        }),
        ('Tallas de Uniformes/EPP', {
            'fields': (
                'shirt_size',
                'pants_size',
                'shoe_size',
                'glove_size',
                'helmet_size'
            ),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': (
                'is_active',
                'termination_date',
                'termination_reason',
                'notes'
            )
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']
    inlines = [EmergencyContactInline]

    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = [
        'personnel',
        'name',
        'relationship',
        'phone',
        'is_primary'
    ]
    list_filter = ['relationship', 'is_primary']
    search_fields = ['name', 'phone', 'personnel__employee_code']
    ordering = ['personnel', '-is_primary', 'name']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = [
        'personnel',
        'record_type',
        'record_date',
        'description',
        'is_confidential',
        'created_at'
    ]
    list_filter = [
        'record_type',
        'is_confidential',
        'requires_followup',
        'record_date'
    ]
    search_fields = [
        'personnel__employee_code',
        'personnel__first_name',
        'personnel__last_name',
        'description',
        'diagnosis'
    ]
    ordering = ['-record_date']
    date_hierarchy = 'record_date'

    fieldsets = (
        ('Personal', {
            'fields': ('personnel',)
        }),
        ('Información del Registro', {
            'fields': (
                'record_type',
                'record_date',
                'description',
                'diagnosis'
            )
        }),
        ('Fechas', {
            'fields': (
                'start_date',
                'end_date'
            )
        }),
        ('Información Médica', {
            'fields': (
                'doctor_name',
                'clinic_hospital',
                'document'
            )
        }),
        ('Seguimiento', {
            'fields': (
                'requires_followup',
                'followup_date',
                'is_confidential',
                'notes'
            )
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CertificationType)
class CertificationTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'name',
        'validity_period_days',
        'is_mandatory',
        'requires_renewal',
        'is_active'
    ]
    list_filter = ['is_mandatory', 'requires_renewal', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['name']


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = [
        'personnel',
        'certification_type',
        'issue_date',
        'expiration_date',
        'is_valid',
        'revoked',
        'status_display'
    ]
    list_filter = [
        'is_valid',
        'revoked',
        'certification_type',
        'issue_date',
        'expiration_date'
    ]
    search_fields = [
        'personnel__employee_code',
        'personnel__first_name',
        'personnel__last_name',
        'certification_number',
        'issuing_authority'
    ]
    ordering = ['-expiration_date']
    date_hierarchy = 'expiration_date'

    fieldsets = (
        ('Personal y Tipo', {
            'fields': (
                'personnel',
                'certification_type'
            )
        }),
        ('Información del Certificado', {
            'fields': (
                'certification_number',
                'issuing_authority',
                'issue_date',
                'expiration_date',
                'certificate_document'
            )
        }),
        ('Estado', {
            'fields': (
                'is_valid',
                'revoked',
                'revocation_reason',
                'revocation_date'
            )
        }),
        ('Renovación', {
            'fields': (
                'renewal_notification_sent',
                'renewal_notification_date',
                'notes'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = [
        'personnel',
        'metric_date',
        'period',
        'pallets_moved',
        'hours_worked',
        'productivity_rate',
        'supervisor_rating'
    ]
    list_filter = [
        'period',
        'metric_date',
        'evaluated_by'
    ]
    search_fields = [
        'personnel__employee_code',
        'personnel__first_name',
        'personnel__last_name'
    ]
    ordering = ['-metric_date']
    date_hierarchy = 'metric_date'

    fieldsets = (
        ('Personal y Período', {
            'fields': (
                'personnel',
                'metric_date',
                'period'
            )
        }),
        ('Métricas Operativas', {
            'fields': (
                'pallets_moved',
                'hours_worked',
                'productivity_rate'
            )
        }),
        ('Indicadores de Calidad', {
            'fields': (
                'errors_count',
                'accidents_count'
            )
        }),
        ('Evaluación del Supervisor', {
            'fields': (
                'supervisor_rating',
                'supervisor_comments',
                'evaluated_by'
            )
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['productivity_rate', 'created_at', 'updated_at']


# ======================================
# NUEVOS MODELOS - SISTEMA ESCALABLE
# ======================================

@admin.register(PerformanceMetricType)
class PerformanceMetricTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'metric_type',
        'weight',
        'is_required',
        'is_active',
        'display_order'
    ]
    list_filter = ['metric_type', 'is_required', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['display_order', 'name']

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'code',
                'description',
                'metric_type',
                'unit'
            )
        }),
        ('Validación', {
            'fields': (
                'min_value',
                'max_value'
            )
        }),
        ('Configuración', {
            'fields': (
                'weight',
                'is_required',
                'is_active',
                'display_order'
            )
        }),
        ('Aplicabilidad', {
            'fields': (
                'applicable_position_types',
            ),
            'description': 'Seleccione los tipos de posición donde aplica esta métrica'
        }),
        ('Ayuda', {
            'fields': ('help_text',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class EvaluationMetricValueInline(admin.TabularInline):
    model = EvaluationMetricValue
    extra = 0
    fields = ['metric_type', 'numeric_value', 'text_value', 'boolean_value', 'comments']
    readonly_fields = []


@admin.register(PerformanceEvaluation)
class PerformanceEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'personnel',
        'evaluation_date',
        'period',
        'overall_score',
        'evaluated_by',
        'is_draft',
        'submitted_at'
    ]
    list_filter = [
        'period',
        'is_draft',
        'evaluation_date',
        'evaluated_by'
    ]
    search_fields = [
        'personnel__employee_code',
        'personnel__first_name',
        'personnel__last_name'
    ]
    ordering = ['-evaluation_date']
    date_hierarchy = 'evaluation_date'
    inlines = [EvaluationMetricValueInline]

    fieldsets = (
        ('Personal y Período', {
            'fields': (
                'personnel',
                'evaluation_date',
                'period',
                'evaluated_by'
            )
        }),
        ('Puntuación', {
            'fields': (
                'overall_score',
            ),
            'description': 'Calculado automáticamente basado en las métricas'
        }),
        ('Comentarios', {
            'fields': ('comments',)
        }),
        ('Estado', {
            'fields': (
                'is_draft',
                'submitted_at'
            )
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['overall_score', 'created_at', 'updated_at', 'submitted_at']


@admin.register(EvaluationMetricValue)
class EvaluationMetricValueAdmin(admin.ModelAdmin):
    list_display = [
        'evaluation',
        'metric_type',
        'get_display_value',
        'created_at'
    ]
    list_filter = ['metric_type', 'created_at']
    search_fields = [
        'evaluation__personnel__employee_code',
        'metric_type__name'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Evaluación y Métrica', {
            'fields': (
                'evaluation',
                'metric_type'
            )
        }),
        ('Valores', {
            'fields': (
                'numeric_value',
                'text_value',
                'boolean_value'
            ),
            'description': 'Complete el valor según el tipo de métrica'
        }),
        ('Comentarios', {
            'fields': ('comments',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_display_value(self, obj):
        return obj.get_display_value()
    get_display_value.short_description = 'Valor'
