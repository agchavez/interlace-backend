"""
ViewSets para catalogos del modulo Tokens: Materiales, Unidades de Medida
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import django_filters

from ..models import Material, UnitOfMeasure, OvertimeTypeModel, OvertimeReasonModel
from ..serializers import (
    MaterialSerializer, UnitOfMeasureSerializer,
    OvertimeTypeModelSerializer, OvertimeReasonModelSerializer,
)


class MaterialFilter(django_filters.FilterSet):
    """Filtros para Material"""
    category = django_filters.CharFilter(lookup_expr='iexact')
    requires_return = django_filters.BooleanFilter()

    class Meta:
        model = Material
        fields = ['category', 'requires_return']


class MaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Materiales.

    Endpoints:
    - GET /api/tokens/materials/ - Listar materiales
    - POST /api/tokens/materials/ - Crear material
    - GET /api/tokens/materials/{id}/ - Detalle de material
    - PUT/PATCH /api/tokens/materials/{id}/ - Actualizar material
    - DELETE /api/tokens/materials/{id}/ - Eliminar material
    - GET /api/tokens/materials/categories/ - Listar categorias unicas
    """
    queryset = Material.objects.select_related('unit_of_measure').all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MaterialFilter
    search_fields = ['code', 'name', 'description', 'category']
    ordering_fields = ['code', 'name', 'category', 'unit_value', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Retorna lista de categorias unicas"""
        categories = Material.objects.values_list(
            'category', flat=True
        ).exclude(category='').distinct().order_by('category')
        return Response(list(categories))


class UnitOfMeasureViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Unidades de Medida.

    Endpoints:
    - GET /api/tokens/units/ - Listar unidades
    - POST /api/tokens/units/ - Crear unidad
    - GET /api/tokens/units/{id}/ - Detalle de unidad
    - PUT/PATCH /api/tokens/units/{id}/ - Actualizar unidad
    - DELETE /api/tokens/units/{id}/ - Eliminar unidad
    """
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['code', 'name', 'abbreviation']
    ordering_fields = ['code', 'name']
    ordering = ['name']


class OvertimeTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Tipos de Horas Extra.

    Endpoints:
    - GET /api/tokens/overtime-types/ - Listar tipos
    - POST /api/tokens/overtime-types/ - Crear tipo
    - GET /api/tokens/overtime-types/{id}/ - Detalle
    - PUT/PATCH /api/tokens/overtime-types/{id}/ - Actualizar
    - DELETE /api/tokens/overtime-types/{id}/ - Eliminar
    """
    queryset = OvertimeTypeModel.objects.all()
    serializer_class = OvertimeTypeModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'default_multiplier']
    ordering = ['name']


class OvertimeReasonViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Motivos de Horas Extra.

    Endpoints:
    - GET /api/tokens/overtime-reasons/ - Listar motivos
    - POST /api/tokens/overtime-reasons/ - Crear motivo
    - GET /api/tokens/overtime-reasons/{id}/ - Detalle
    - PUT/PATCH /api/tokens/overtime-reasons/{id}/ - Actualizar
    - DELETE /api/tokens/overtime-reasons/{id}/ - Eliminar
    """
    queryset = OvertimeReasonModel.objects.all()
    serializer_class = OvertimeReasonModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name']
    ordering = ['name']
