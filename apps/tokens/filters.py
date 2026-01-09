"""
Filtros para el módulo de tokens
"""
import django_filters
from .models import TokenRequest


class TokenRequestFilter(django_filters.FilterSet):
    """Filtros para TokenRequest"""

    # Filtros de fecha
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Creado después de'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Creado antes de'
    )
    valid_from_after = django_filters.DateTimeFilter(
        field_name='valid_from',
        lookup_expr='gte',
        label='Válido desde después de'
    )
    valid_until_before = django_filters.DateTimeFilter(
        field_name='valid_until',
        lookup_expr='lte',
        label='Válido hasta antes de'
    )

    # Filtros de relación
    personnel = django_filters.NumberFilter(
        field_name='personnel_id',
        label='ID del beneficiario'
    )
    requested_by = django_filters.NumberFilter(
        field_name='requested_by_id',
        label='ID del solicitante'
    )
    distributor_center = django_filters.NumberFilter(
        field_name='distributor_center_id',
        label='ID del centro de distribución'
    )

    # Filtros de texto
    display_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Número de token'
    )
    personnel_code = django_filters.CharFilter(
        field_name='personnel__employee_code',
        lookup_expr='icontains',
        label='Código de empleado'
    )

    # Filtros múltiples
    status = django_filters.MultipleChoiceFilter(
        choices=TokenRequest.Status.choices,
        label='Estados'
    )
    token_type = django_filters.MultipleChoiceFilter(
        choices=TokenRequest.TokenType.choices,
        label='Tipos de token'
    )

    class Meta:
        model = TokenRequest
        fields = [
            'token_type',
            'status',
            'personnel',
            'requested_by',
            'distributor_center',
            'display_number',
            'personnel_code',
            'created_after',
            'created_before',
            'valid_from_after',
            'valid_until_before',
        ]
