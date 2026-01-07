"""
Vistas para mantenimiento de catálogos y tablas maestras
Este módulo centraliza los endpoints CRUD para todas las tablas de configuración
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models.organization import Area, Department
from ..serializers.personnel_serializers import AreaSerializer, DepartmentSerializer
from ..permissions import IsSupervisorOrAbove


class AreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Áreas (CRUD)

    Endpoints:
    - GET /api/personnel/areas/ - Listar áreas
    - POST /api/personnel/areas/ - Crear área
    - GET /api/personnel/areas/{id}/ - Obtener área
    - PUT/PATCH /api/personnel/areas/{id}/ - Actualizar área
    - DELETE /api/personnel/areas/{id}/ - Eliminar área (soft delete)

    Query params:
    - is_active: true/false - Filtrar por estado activo
    - search: texto - Buscar en nombre, código, descripción
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAbove]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Permitir filtrar por is_active"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def perform_destroy(self, instance):
        """Soft delete - solo marca como inactivo"""
        # Verificar si tiene departamentos activos
        if instance.departments.filter(is_active=True).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': 'No se puede eliminar un área con departamentos activos'
            })
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Reactivar un área
        POST /api/personnel/areas/{id}/activate/
        """
        area = self.get_object()
        area.is_active = True
        area.save()
        serializer = self.get_serializer(area)
        return Response(serializer.data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Departamentos (CRUD)

    Endpoints:
    - GET /api/personnel/departments/ - Listar departamentos
    - POST /api/personnel/departments/ - Crear departamento
    - GET /api/personnel/departments/{id}/ - Obtener departamento
    - PUT/PATCH /api/personnel/departments/{id}/ - Actualizar departamento
    - DELETE /api/personnel/departments/{id}/ - Eliminar departamento (soft delete)

    Query params:
    - is_active: true/false - Filtrar por estado activo
    - area: id - Filtrar por área
    - search: texto - Buscar en nombre, código, descripción
    """
    queryset = Department.objects.select_related('area').all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAbove]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['area__name', 'name']
    filterset_fields = ['area', 'is_active']
    pagination_class = None  # Desactivar paginación para devolver todos los departamentos

    def get_queryset(self):
        """Permitir filtrar por is_active y area"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        area = self.request.query_params.get('area', None)
        if area:
            queryset = queryset.filter(area_id=area)

        return queryset

    def perform_destroy(self, instance):
        """Soft delete - solo marca como inactivo"""
        # Verificar si tiene personal activo
        if instance.personnel_in_department.filter(is_active=True).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': 'No se puede eliminar un departamento con personal activo'
            })
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Reactivar un departamento
        POST /api/personnel/departments/{id}/activate/
        """
        department = self.get_object()
        department.is_active = True
        department.save()
        serializer = self.get_serializer(department)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_area(self, request):
        """
        Obtener departamentos agrupados por área
        GET /api/personnel/departments/by_area/

        Returns:
        {
            "area_id": {
                "area_name": "...",
                "departments": [...]
            }
        }
        """
        queryset = self.get_queryset()
        result = {}

        for dept in queryset:
            area_id = str(dept.area.id)
            if area_id not in result:
                result[area_id] = {
                    'area_id': dept.area.id,
                    'area_name': dept.area.get_code_display(),
                    'area_code': dept.area.code,
                    'departments': []
                }
            result[area_id]['departments'].append(self.get_serializer(dept).data)

        return Response(result)
