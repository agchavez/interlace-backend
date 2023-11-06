from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from django_filters import rest_framework as filters

from ..models import InventoryModel, InventoryMovementModel
from ..serializers import InventorySerializer, InventoryMovementSerializer


# Filtros de inventario
class InventoryFilter(filters.FilterSet):
    class Meta:
        model = InventoryModel
        fields = {
            'product': ['exact'],
            'distributor_center': ['exact'],
            'expiration_date': ['exact', 'lte', 'gte'],
        }


# Filtros de movimientos de inventario
class InventoryMovementFilter(filters.FilterSet):
    class Meta:
        model = InventoryMovementModel
        fields = {
            'product': ['exact'],
            'distributor_center': ['exact'],
            'date': ['exact', 'lte', 'gte'],
            'movement_type': ['exact'],
            'user': ['exact'],
        }


# Vista de inventario
class InventoryViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = InventoryModel.objects.all()
    serializer_class = InventorySerializer
    filterset_class = InventoryFilter


# Vista de movimientos de inventario
class InventoryMovementViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = InventoryMovementModel.objects.all()
    serializer_class = InventoryMovementSerializer
    filterset_class = InventoryMovementFilter

