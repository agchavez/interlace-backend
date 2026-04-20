"""
Filtros para el ciclo del camión
"""
import django_filters
from django.db.models import Q
from apps.truck_cycle.models.core import PautaModel


class PautaFilter(django_filters.FilterSet):
    status = django_filters.BaseInFilter(field_name='status', lookup_expr='in')
    operational_date_after = django_filters.DateFilter(field_name='operational_date', lookup_expr='gte')
    operational_date_before = django_filters.DateFilter(field_name='operational_date', lookup_expr='lte')
    truck = django_filters.NumberFilter(field_name='truck', lookup_expr='exact')
    transport_number = django_filters.CharFilter(field_name='transport_number', lookup_expr='icontains')
    is_reload = django_filters.BooleanFilter(field_name='is_reload')
    # "Mis pautas" en un rol dado — usa el personnel_profile del user autenticado.
    assigned_role = django_filters.CharFilter(method='filter_assigned_role')
    # Chofer vendedor: pautas donde truck.primary_driver=me OR assignment DELIVERY_DRIVER=me.
    my_vendor_pautas = django_filters.BooleanFilter(method='filter_my_vendor_pautas')

    class Meta:
        model = PautaModel
        fields = ['status', 'operational_date_after', 'operational_date_before', 'truck', 'transport_number', 'is_reload']

    def filter_assigned_role(self, queryset, name, value):
        """
        Devuelve pautas con una asignación activa en el rol dado (PICKER, COUNTER, etc.)
        para el personnel_profile del usuario autenticado.
        """
        if not value:
            return queryset
        request = self.request
        if not request or not request.user.is_authenticated:
            return queryset.none()
        try:
            profile = request.user.personnel_profile
        except Exception:
            return queryset.none()
        return queryset.filter(
            assignments__role=value.upper(),
            assignments__is_active=True,
            assignments__personnel=profile,
        ).distinct()

    def filter_my_vendor_pautas(self, queryset, name, value):
        """
        Pautas del chofer vendedor autenticado:
        - El cami\xf3n tiene primary_driver = mi perfil, O
        - Hay una assignment activa con role=DELIVERY_DRIVER para m\xed.
        """
        if not value:
            return queryset
        request = self.request
        if not request or not request.user.is_authenticated:
            return queryset.none()
        try:
            profile = request.user.personnel_profile
        except Exception:
            return queryset.none()
        return queryset.filter(
            Q(truck__primary_driver=profile)
            | Q(assignments__role='DELIVERY_DRIVER', assignments__is_active=True, assignments__personnel=profile)
        ).distinct()
