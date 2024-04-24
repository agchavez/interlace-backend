from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, \
    DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework import status
from ..exceptions.order_detail import OrderDetailExist, OutOrderExist, PermissionDenied
# LOCAL
from ..models.order import OrderModel
from ..models.history import OrderHistoryModel
from ..models.detail import OrderDetailModel
from ..models.out_order import OutOrderModel

from ..serializers import OrderSerializer, OrderDetailSerializer, OrderHistorySerializer, OutOrderSerializer

from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import filters

from ..utils.order import validate_and_create_order, insert_order_detail_to_inventory_movement
from ...tracker.exceptions.tracker import FileTooLarge, FileNotExists
from ...user.views.user import CustomAccessPermission

class OrderFilter(django_filters.FilterSet):
    status_choice = django_filters.MultipleChoiceFilter(
        choices=OrderModel.OrderStatus.choices,
        field_name='status',

    )
    class Meta:
        model = OrderModel
        fields = {
            'status': ['exact'],
            'id': ['exact'],
            'location': ['exact'],
            'distributor_center': ['exact'],
        }

# ViewSet de ordenes
class OrderViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet,
                   DestroyModelMixin):
    queryset = OrderModel.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'id'

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = OrderFilter

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
        # solo si distributions_centers solo tiene un centro de distribucion
        user = self.request
        try:
            if len(user.distributions_centers) == 1:
                cd = user.distributions_centers.first()
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

    # Cargar desde un excel los detalles de una orden
    @action(detail=False, methods=['post'], url_path='load-excel')
    def load_excel(self, request):
        order, list_data_error = validate_and_create_order(request)
        return Response({
            'order': OrderSerializer(order).data,
            'order_detail': OrderDetailSerializer(OrderDetailModel.objects.filter(order=order), many=True).data,
            'errors': list_data_error,
        }, status=status.HTTP_201_CREATED)



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


# Vista para salida de ordenes
class OutOrderViewSet(CreateModelMixin, GenericViewSet):
    queryset = OutOrderModel.objects.all()
    serializer_class = OutOrderSerializer
    lookup_field = 'id'
    permission_classes = [CustomAccessPermission]
    PERMISSION_MAPPING = {
        'GET': ['order.view_outordermodel'],
        'POST': ['order.add_outordermodel'],
        'PUT': ['order.change_outordermodel'],
        'PATCH': ['order.change_outordermodel'],
        'DELETE': ['order.delete_outordermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        order_id = request.data.get('order')
        order = get_object_or_404(OrderModel, id=order_id)
        document = request.data.get("document")
        user = request.user
        try:
            if user.centro_distribucion is None or user.centro_distribucion.id != order.distributor_center.id:
                raise PermissionDenied()
        except:
            raise PermissionDenied()
        if document is not None:
            if document.size > 20 * 1024 * 1024:
                raise FileTooLarge
        if order.status != OrderModel.OrderStatus.PENDING:
            raise OutOrderExist()

        if OutOrderModel.objects.filter(order=order).exists():
            raise OutOrderExist()

        result = super(OutOrderViewSet, self).create(request, *args, **kwargs)
        if document is not None:
            instance = OutOrderModel.objects.get(id=result.data['id'])
            content = document.read()
            instance.document = content
            name = request.data.get("document_name")
            if name is not None:
                instance.document_name = name
            instance.save()
        # actualizar el estado de la orden
        order.status = OrderModel.OrderStatus.COMPLETED
        order.save()

        # hacer los movimientos de inventario de salida
        insert_order_detail_to_inventory_movement(order, request.user.id)
        return result

    @action(detail=True, methods=['get'], url_path='get-file')
    def getFile(self, request, *args, **kwargs):
        out_order = self.get_object()
        archivo = out_order.document
        if not archivo:
            raise FileNotExists
        response = HttpResponse(archivo, content_type='application/octet-stream', )
        response['Content-Disposition'] = f'attachment; filename="{out_order.document_name}"'
        return response
