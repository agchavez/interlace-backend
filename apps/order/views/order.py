from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, \
    DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from ..exceptions.order_detail import OrderDetailExist
# LOCAL
from ..models.order import OrderModel
from ..models.history import OrderHistoryModel
from ..models.detail import OrderDetailModel

from ..serializers import OrderSerializer, OrderDetailSerializer, OrderHistorySerializer
from ...user.views.user import CustomAccessPermission


# ViewSet de ordenes
class OrderViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet,
                   DestroyModelMixin):
    queryset = OrderModel.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'id'
    permission_classes = [CustomAccessPermission]
    PERMISSION_MAPPING = {
        'GET': ['order.view_ordermodel'],
        'POST': ['order.add_ordermodel'],
        'PUT': ['order.change_ordermodel'],
        'PATCH': ['order.change_ordermodel'],
        'DELETE': ['order.delete_ordermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    # Solo ver las ordenes del centro de distribucion del usuario
    def get_queryset(self):
        queryset = OrderModel.objects.all()
        user = self.request.user
        try:
            cd = user.distributor_center
            queryset = queryset.filter(distributor_center=cd)
        except:
            pass
        return queryset


# ViewSet de detalles de ordenes
class OrderDetailViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet,
                         DestroyModelMixin):
    queryset = OrderDetailModel.objects.all()
    serializer_class = OrderDetailSerializer
    lookup_field = 'id'
    permission_classes = [CustomAccessPermission]
    PERMISSION_MAPPING = {
        'GET': ['order.view_ordermodel'],
        'POST': ['order.add_ordermodel'],
        'PUT': ['order.change_ordermodel'],
        'PATCH': ['order.change_ordermodel'],
        'DELETE': ['order.delete_ordermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

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
    permission_classes = [CustomAccessPermission]
    PERMISSION_MAPPING = {
        'GET': ['order.view_ordermodel'],
        'POST': ['order.add_ordermodel'],
        'PUT': ['order.change_ordermodel'],
        'PATCH': ['order.change_ordermodel'],
        'DELETE': ['order.delete_ordermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])
