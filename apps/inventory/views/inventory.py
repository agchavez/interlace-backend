from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from ..models import InventoryMovementModel
from ..serializers import InventoryMovementSerializer



# Filtros de movimientos de inventario
class InventoryMovementFilter(filters.FilterSet):
    class Meta:
        model = InventoryMovementModel
        fields = {
            'movement_type': ['exact'],
            'user': ['exact'],
        }
# Vista de movimientos de inventario
class InventoryMovementViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = InventoryMovementModel.objects.all()
    serializer_class = InventoryMovementSerializer
    filterset_class = InventoryMovementFilter
    filter_backends = [DjangoFilterBackend]

