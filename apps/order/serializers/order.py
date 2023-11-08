from django.db.models import Sum

from ..models import OrderModel, OrderDetailModel, OrderHistoryModel

from ..exceptions.order_detail import QuantityExceeded
from apps.maintenance.serializer import ProductModelSerializer
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
        # la suma de las cantidades de los productos no puede ser mayor a la cantidad disponible de tracker detail product
        quantity = attrs.get('quantity')
        # veridicar si hay mas registros en la orden del mismo tracker detail product y sumarlos
        if self.instance:
            sum_quantity = OrderDetailModel.objects.filter(tracker_detail_product=attrs.get('tracker_detail_product'), status__not_in=[OrderModel.OrderStatus.COMPLETED]
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
        total_quantity = boxes_pre_pallet * (value + quantity)
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

# Serializer de ordenes
class OrderSerializer(serializers.ModelSerializer):
    order_detail = OrderDetailSerializer(many=True, read_only=True)
    class Meta:
        model = OrderModel
        fields = '__all__'
