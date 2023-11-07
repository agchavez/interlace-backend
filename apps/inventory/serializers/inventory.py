from rest_framework import serializers

from ..models import InventoryMovementModel
from apps.maintenance.serializer import ProductModelSerializer
from apps.user.serializers import UserSerializer

class InventoryMovementSerializer(serializers.ModelSerializer):
    product_data = ProductModelSerializer(source='product', read_only=True)
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = InventoryMovementModel
        fields = '__all__'
