from ..models import OrderModel, OrderDetailModel, OrderHistoryModel
from rest_framework import serializers

# Serializer de historico de ordenes
class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryModel
        fields = '__all__'

# Serializer de detalle de ordenes
class OrderDetailSerializer(serializers.ModelSerializer):
    order_detail_history = OrderHistorySerializer(many=True)
    class Meta:
        model = OrderDetailModel
        fields = '__all__'

# Serializer de ordenes
class OrderSerializer(serializers.ModelSerializer):
    order_detail = OrderDetailSerializer(many=True)
    class Meta:
        model = OrderModel
        fields = '__all__'
