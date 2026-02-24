"""
Filtros personalizados para el módulo de personal
"""
from django_filters import rest_framework as filters
from datetime import date, timedelta
from .models.personnel import PersonnelProfile
from .models.medical import MedicalRecord
from .models.certification import Certification
from .models.performance import PerformanceMetric


class PersonnelProfileFilter(filters.FilterSet):
    """Filtros para perfiles de personal"""
    employee_code = filters.CharFilter(lookup_expr='icontains')
    full_name = filters.CharFilter(method='filter_full_name')
    hierarchy_level = filters.CharFilter()
    position_type = filters.CharFilter()
    area = filters.NumberFilter(field_name='area__id')
    department = filters.NumberFilter(field_name='department__id')
    primary_distributor_center = filters.NumberFilter(field_name='primary_distributor_center__id')
    any_distributor_center = filters.NumberFilter(method='filter_any_distributor_center')
    is_active = filters.BooleanFilter()
    hire_date_from = filters.DateFilter(field_name='hire_date', lookup_expr='gte')
    hire_date_to = filters.DateFilter(field_name='hire_date', lookup_expr='lte')
    has_valid_certifications = filters.BooleanFilter(method='filter_valid_certifications')
    certifications_expiring = filters.BooleanFilter(method='filter_expiring_certifications')
    supervisor = filters.NumberFilter(field_name='immediate_supervisor__id')

    class Meta:
        model = PersonnelProfile
        fields = [
            'employee_code', 'hierarchy_level', 'position_type',
            'area', 'department', 'primary_distributor_center', 'is_active'
        ]

    def filter_full_name(self, queryset, name, value):
        return queryset.filter(
            first_name__icontains=value
        ) | queryset.filter(
            last_name__icontains=value
        )

    def filter_valid_certifications(self, queryset, name, value):
        if value:
            return queryset.filter(
                certifications__is_valid=True
            ).distinct()
        return queryset.exclude(
            certifications__is_valid=True
        ).distinct()

    def filter_expiring_certifications(self, queryset, name, value):
        if value:
            threshold = date.today() + timedelta(days=30)
            return queryset.filter(
                certifications__expiration_date__lte=threshold,
                certifications__expiration_date__gte=date.today(),
                certifications__is_valid=True
            ).distinct()
        return queryset

    def filter_any_distributor_center(self, queryset, name, value):
        """Filtra por cualquier centro de distribución (principal o adicional)"""
        return queryset.filter(distributor_centers__id=value).distinct()


class MedicalRecordFilter(filters.FilterSet):
    """Filtros para registros médicos"""
    personnel = filters.NumberFilter()
    record_type = filters.CharFilter()
    record_date_from = filters.DateFilter(field_name='record_date', lookup_expr='gte')
    record_date_to = filters.DateFilter(field_name='record_date', lookup_expr='lte')
    is_confidential = filters.BooleanFilter()
    requires_followup = filters.BooleanFilter()

    class Meta:
        model = MedicalRecord
        fields = ['personnel', 'record_type', 'is_confidential', 'requires_followup']


class CertificationFilter(filters.FilterSet):
    """Filtros para certificaciones"""
    personnel = filters.NumberFilter()
    certification_type = filters.NumberFilter()
    is_valid = filters.BooleanFilter()
    is_expiring_soon = filters.BooleanFilter(method='filter_expiring_soon')
    is_expired = filters.BooleanFilter(method='filter_expired')
    expiration_date_from = filters.DateFilter(
        field_name='expiration_date',
        lookup_expr='gte'
    )
    expiration_date_to = filters.DateFilter(
        field_name='expiration_date',
        lookup_expr='lte'
    )

    class Meta:
        model = Certification
        fields = ['personnel', 'certification_type', 'is_valid']

    def filter_expiring_soon(self, queryset, name, value):
        if value:
            threshold = date.today() + timedelta(days=30)
            return queryset.filter(
                expiration_date__lte=threshold,
                expiration_date__gte=date.today(),
                is_valid=True
            )
        return queryset

    def filter_expired(self, queryset, name, value):
        if value:
            return queryset.filter(expiration_date__lt=date.today())
        return queryset.filter(expiration_date__gte=date.today())


class PerformanceMetricFilter(filters.FilterSet):
    """Filtros para métricas de desempeño"""
    personnel = filters.NumberFilter()
    period = filters.CharFilter()
    metric_date_from = filters.DateFilter(field_name='metric_date', lookup_expr='gte')
    metric_date_to = filters.DateFilter(field_name='metric_date', lookup_expr='lte')
    evaluated_by = filters.NumberFilter()
    min_productivity = filters.NumberFilter(
        field_name='productivity_rate',
        lookup_expr='gte'
    )
    max_productivity = filters.NumberFilter(
        field_name='productivity_rate',
        lookup_expr='lte'
    )

    class Meta:
        model = PerformanceMetric
        fields = ['personnel', 'period', 'evaluated_by']
