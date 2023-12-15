from django.db.models import Sum

from ..models.order import OrderModel
from ..models.history import OrderHistoryModel
from ..models.detail import OrderDetailModel
from ..models.out_order import OutOrderModel

from ..exceptions.order_detail import QuantityExceeded, OrderNotCompleted
from apps.maintenance.serializer import ProductModelSerializer, LocationModelSerializer
from rest_framework import serializers

# Serializer de historico de ordenes
class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryModel
        fields = '__all__'

# Serializer de detalle de ordenes
class OrderDetailSerializer(serializers.ModelSerializer):
    order_detail_history = OrderHistorySerializer(many=True, read_only=True)
    product_data = ProductModelSerializer(source='tracker_detail_product.tracker_detail.product', read_only=True)
    tracking_id = serializers.IntegerField(source='tracker_detail_product.tracker_detail.tracker.id', read_only=True)
    expiration_date = serializers.DateField(source='tracker_detail_product.expiration_date', read_only=True)
    def validate(self, attrs):

        # Nose puede editar una orden que no esta en estado COMPLETED o IN_PROCESS
        if self.instance:
            if self.instance.order.status in [OrderModel.OrderStatus.COMPLETED, OrderModel.OrderStatus.IN_PROCESS]:
                raise OrderNotCompleted()

        # la suma de las cantidades de los productos no puede ser mayor a la cantidad disponible de tracker detail product
        quantity = attrs.get('quantity')
        # veridicar si hay mas registros en la orden del mismo tracker detail product y sumarlos
        if self.instance:
            sum_quantity = OrderDetailModel.objects.filter(tracker_detail_product=attrs.get('tracker_detail_product'), order__status__in=[OrderModel.OrderStatus.IN_PROCESS, OrderModel.OrderStatus.PENDING]
                                                           ).exclude(
                id=self.instance.id).aggregate(Sum('quantity'))
            if sum_quantity.get('quantity__sum') is None:
                sum_quantity = {'quantity__sum': 0}
        else:
            sum_quantity = OrderDetailModel.objects.filter(tracker_detail_product=attrs.get('tracker_detail_product')).aggregate(
                Sum('quantity'
                    ''))
            if sum_quantity.get('quantity__sum') is None:
                sum_quantity = {'quantity__sum': 0}
        value = sum_quantity.get('quantity__sum')
        boxes_pre_pallet = attrs.get('tracker_detail_product').tracker_detail.product.boxes_pre_pallet
        # catidad total es la cantidad de cajas por pallet por toda la cantidad de pallets
        total_quantity = value + quantity
        if total_quantity > attrs.get(
                'tracker_detail_product').available_quantity:
            raise QuantityExceeded()
        return attrs

    # cuando se registra la cantidad disponible es la misma que la cantidad
    def create(self, validated_data):
        validated_data['quantity_available'] = validated_data.get('quantity')
        return super(OrderDetailSerializer, self).create(validated_data)

    # cuando se actualiza la cantidad disponible es la misma que la cantidad
    def update(self, instance, validated_data):
        validated_data['quantity_available'] = validated_data.get('quantity')
        return super(OrderDetailSerializer, self).update(instance, validated_data)
    class Meta:
        model = OrderDetailModel
        fields = '__all__'
        read_only_fields = ('quantity_available',)


# Serializer de ordenes de salida
class OutOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutOrderModel
        fields = '__all__'

# Serializer de ordenes
class OrderSerializer(serializers.ModelSerializer):
    order_detail = OrderDetailSerializer(many=True, read_only=True)
    location_data = LocationModelSerializer(source='location', read_only=True)
    out_order = OutOrderSerializer(read_only=True)

    # No se pueden editar las ordenes que estan en estado COMPLETED o IN_PROCESS
    def validate(self, attrs):
        if self.instance:
            if self.instance.status in [OrderModel.OrderStatus.COMPLETED, OrderModel.OrderStatus.IN_PROCESS]:
                raise OrderNotCompleted()
        return attrs
    class Meta:
        model = OrderModel
        fields = '__all__'


