from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from ..exceptions.order_detail import OrderDetailExist
# LOCAL
from ..models.order import OrderModel
from ..models.history import OrderHistoryModel
from ..models.detail import OrderDetailModel

from ..serializers import OrderSerializer, OrderDetailSerializer, OrderHistorySerializer
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import filters

class OrderFilter(django_filters.FilterSet):
    class Meta:
        model = OrderModel
        fields = {
            'status': ['exact'],
            'id': ['exact'],
            'location': ['exact'],
            'distributor_center': ['exact'],
        }

# ViewSet de ordenes
class OrderViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet, DestroyModelMixin):
    queryset = OrderModel.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = OrderFilter


# ViewSet de detalles de ordenes
class OrderDetailViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet, DestroyModelMixin):
    queryset = OrderDetailModel.objects.all()
    serializer_class = OrderDetailSerializer
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        # buscar si ya existe un registro con el mismo tracker detail product y la misma orden
        order = request.data.get('order')
        tracker_detail_product = request.data.get('tracker_detail_product')
        order_detail = OrderDetailModel.objects.filter(order=order, tracker_detail_product=tracker_detail_product)
        if order_detail:
            raise OrderDetailExist()
        return super(OrderDetailViewSet, self).create(request, *args, **kwargs)


# ViewSet de historico de ordenes
class OrderHistoryViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = OrderHistoryModel.objects.all()
    serializer_class = OrderHistorySerializer
    lookup_field = 'id'
