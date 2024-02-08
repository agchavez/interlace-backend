from rest_framework import serializers

from ..models import InventoryMovementModel
from apps.maintenance.serializer import ProductModelSerializer
from apps.user.serializers import UserSerializer
from ...tracker.models import TrackerDetailProductModel


class InventoryMovementSerializer(serializers.ModelSerializer):
    product_data = ProductModelSerializer(source='product', read_only=True)
    distributor_center_name = serializers.CharField(source='tracker_detail_product.tracker_detail.tracker.distributor_center.name', read_only=True)
    product_name = serializers.CharField(source='tracker_detail_product.tracker_detail.product.name', read_only=True)
    product_sap_code = serializers.CharField(source='tracker_detail_product.tracker_detail.product.sap_code', read_only=True)
    tracker = serializers.CharField(source='tracker_detail_product.tracker_detail.tracker.id', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    final_quantity = serializers.SerializerMethodField('get_final_quantity')

    def get_final_quantity(self, obj):
        if obj.is_applied:
            return obj.initial_quantity + obj.quantity
        else:
            return None
    class Meta:
        model = InventoryMovementModel
        fields = '__all__'

# Serializer de carga masiva de inventario
class InventoryMovementMassiveSerializer(serializers.Serializer):
    # Lista de movimientos de inventario, cada movimiento es un diccionario con los siguientes campos:
    # tracking_detail_product: id del tracking detail product
    # quantity: cantidad del movimiento
    list = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(max_length=100)
        )
    )
    reason = serializers.CharField(max_length=100)


    def validate_list(self, value):
        for item in value:
            # Verificar que 'tracking_detail_product' esté presente
            if 'tracking_detail_product' not in item:
                raise serializers.ValidationError("Cada elemento debe tener 'tracking_detail_product'.")

            # Verificar que 'quantity' esté presente
            if 'quantity' not in item:
                raise serializers.ValidationError("Cada elemento debe tener 'quantity'.")

            # Verificar que 'tracking_detail_product' existe en TrackerDetailProductModel
            tracking_detail_product_id = item['tracking_detail_product']
            try:
                TrackerDetailProductModel.objects.get(id=tracking_detail_product_id)
            except TrackerDetailProductModel.DoesNotExist:
                raise serializers.ValidationError(f"'tracking_detail_product' {tracking_detail_product_id} no existe.")

        return value