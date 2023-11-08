from django.db.models import Sum

from ..models import OrderModel, OrderDetailModel, OrderHistoryModel
from ..exceptions.order_detail import QuantityExceeded

from rest_framework import serializers

# Serializer de historico de ordenes
class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryModel
        fields = '__all__'

# Serializer de detalle de ordenes
class OrderDetailSerializer(serializers.ModelSerializer):
    order_detail_history = OrderHistorySerializer(many=True, read_only=True)


    def validate(self, attrs):
        # la suma de las cantidades de los productos no puede ser mayor a la cantidad disponible de tracker detail product
        quantity = attrs.get('quantity')
        # veridicar si hay mas registros en la orden del mismo tracker detail product y sumarlos
        if self.instance:
            sum_quantity = OrderDetailModel.objects.filter(tracker_detail_product=attrs.get('tracker_detail_product')).exclude(
                id=self.instance.id).aggregate(Sum('quantity'))
            if sum_quantity.get('quantity__sum') is None:
                sum_quantity = {'quantity__sum': 0}
        else:
            sum_quantity = OrderDetailModel.objects.filter(tracker_detail_product=attrs.get('tracker_detail_product')).aggregate(
                Sum('quantity'))
            if sum_quantity.get('quantity__sum') is None:
                sum_quantity = {'quantity__sum': 0}
        value = sum_quantity.get('quantity__sum')
        if (value + quantity) > attrs.get(
                'tracker_detail_product').quantity:
            raise QuantityExceeded()
        return attrs


    class Meta:
        model = OrderDetailModel
        fields = '__all__'

# Serializer de ordenes
class OrderSerializer(serializers.ModelSerializer):
    order_detail = OrderDetailSerializer(many=True, read_only=True)
    class Meta:
        model = OrderModel
        fields = '__all__'
