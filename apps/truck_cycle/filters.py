"""
Filtros para el ciclo del camión
"""
import django_filters
from apps.truck_cycle.models.core import PautaModel


class PautaFilter(django_filters.FilterSet):
    status = django_filters.BaseInFilter(field_name='status', lookup_expr='in')
    operational_date_after = django_filters.DateFilter(field_name='operational_date', lookup_expr='gte')
    operational_date_before = django_filters.DateFilter(field_name='operational_date', lookup_expr='lte')
    truck = django_filters.NumberFilter(field_name='truck', lookup_expr='exact')
    transport_number = django_filters.CharFilter(field_name='transport_number', lookup_expr='icontains')
    is_reload = django_filters.BooleanFilter(field_name='is_reload')

    class Meta:
        model = PautaModel
        fields = ['status', 'operational_date_after', 'operational_date_before', 'truck', 'transport_number', 'is_reload']
