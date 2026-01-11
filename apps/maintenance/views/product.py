from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import ProductModel, OutputTypeModel

# Serializers
from ..serializer import ProductModelSerializer, OutputTypeModelSerializer
from apps.user.views.user import CustomAccessPermission

class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = ProductModel
        fields = {
            'name': ['exact'],
            'bar_code': ['exact'],
            'id': ['exact'],
            'is_output': ['exact'],
        }


class ProductModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Productos.

    Endpoints:
    - GET /api/maintenance/products/ - Listar productos
    - POST /api/maintenance/products/ - Crear producto
    - GET /api/maintenance/products/{id}/ - Detalle de producto
    - PUT/PATCH /api/maintenance/products/{id}/ - Actualizar producto
    - DELETE /api/maintenance/products/{id}/ - Eliminar producto
    """
    queryset = ProductModel.objects.all()
    serializer_class = ProductModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ('name', 'sap_code', 'brand', 'bar_code')
    filterset_class = ProductFilter
    ordering_fields = ['name', 'sap_code', 'brand', 'created_at']
    ordering = ['name']
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_productmodel'],
        'POST': ['maintenance.add_productmodel'],
        'PUT': ['maintenance.change_productmodel'],
        'PATCH': ['maintenance.change_productmodel'],
        'DELETE': ['maintenance.delete_productmodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])


class OutputTypeModelViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin
        , viewsets.GenericViewSet):
        queryset = OutputTypeModel.objects.all()
        serializer_class = OutputTypeModelSerializer
        filter_backends = [filters.SearchFilter]
        search_fields = ('name')
        permission_classes = [CustomAccessPermission]

        PERMISSION_MAPPING = {
            'GET': ['maintenance.view_outputtypemodel'],
            'POST': ['maintenance.add_outputtypemodel'],
            'PUT': ['maintenance.change_outputtypemodel'],
            'PATCH': ['maintenance.change_outputtypemodel'],
            'DELETE': ['maintenance.delete_outputtypemodel'],
        }

        def get_required_permissions(self, http_method):
            return self.PERMISSION_MAPPING.get(http_method, [])
