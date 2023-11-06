from rest_framework import serializers

from ..models import InventoryModel, InventoryMovementModel
from apps.maintenance.serializer import ProductModelSerializer
class InventorySerializer(serializers.ModelSerializer):
    product_data = ProductModelSerializer(source='product', read_only=True)
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)

    class Meta:
        model = InventoryModel
        fields = '__all__'

class InventoryMovementSerializer(serializers.ModelSerializer):
    product_data = ProductModelSerializer(source='product', read_only=True)
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)

    class Meta:
        model = InventoryMovementModel
        fields = '__all__'
