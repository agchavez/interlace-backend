from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

# LOCAL
from ..models import OrderModel, OrderDetailModel, OrderHistoryModel
from ..serializers import OrderSerializer, OrderDetailSerializer, OrderHistorySerializer


# ViewSet de ordenes
class OrderViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = OrderModel.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'id'


# ViewSet de detalles de ordenes
class OrderDetailViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = OrderDetailModel.objects.all()
    serializer_class = OrderDetailSerializer
    lookup_field = 'id'


# ViewSet de historico de ordenes
class OrderHistoryViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = OrderHistoryModel.objects.all()
    serializer_class = OrderHistorySerializer
    lookup_field = 'id'
