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
    
    # Campos dinámicos que funcionan para ambos flujos
    product_data = serializers.SerializerMethodField()
    tracking_id = serializers.SerializerMethodField()
    expiration_date_display = serializers.SerializerMethodField()
    
    def get_product_data(self, obj):
        product = obj.get_product()
        if product:
            return ProductModelSerializer(product).data
        return None
    
    def get_tracking_id(self, obj):
        if obj.tracker_detail_product:
            return obj.tracker_detail_product.tracker_detail.tracker.id
        return None
    
    def get_expiration_date_display(self, obj):
        if obj.tracker_detail_product:
            return obj.tracker_detail_product.expiration_date
        return obj.expiration_date
    
    def validate(self, attrs):
        # No se puede editar una orden que está en estado COMPLETED o IN_PROCESS
        if self.instance:
            if self.instance.order.status in [OrderModel.OrderStatus.COMPLETED, OrderModel.OrderStatus.IN_PROCESS]:
                raise OrderNotCompleted()

        # Validar que solo se especifique una fuente de producto
        tracker_detail_product = attrs.get('tracker_detail_product')
        product = attrs.get('product')
        
        if tracker_detail_product and product:
            raise serializers.ValidationError("No se puede especificar tanto tracker_detail_product como product")
        
        if not tracker_detail_product and not product:
            raise serializers.ValidationError("Debe especificar tracker_detail_product o product")

        quantity = attrs.get('quantity')

        if tracker_detail_product:
            # VALIDACIÓN ACTUAL - Mantiene la lógica original
            return self._validate_tracker_product(attrs, quantity)
        else:
            # NUEVA VALIDACIÓN - Para productos directos
            return self._validate_direct_product(attrs, quantity)

    def _validate_tracker_product(self, attrs, quantity):
        """Validación para productos con tracker (lógica original)"""
        tracker_detail_product = attrs.get('tracker_detail_product')
        
        # Verificar si hay más registros en la orden del mismo tracker detail product y sumarlos
        if self.instance:
            sum_quantity = OrderDetailModel.objects.filter(
                tracker_detail_product=tracker_detail_product,
                order__status__in=[OrderModel.OrderStatus.IN_PROCESS, OrderModel.OrderStatus.PENDING]
            ).exclude(id=self.instance.id).aggregate(Sum('quantity'))
        else:
            sum_quantity = OrderDetailModel.objects.filter(
                tracker_detail_product=tracker_detail_product
            ).aggregate(Sum('quantity'))
        
        if sum_quantity.get('quantity__sum') is None:
            sum_quantity = {'quantity__sum': 0}
        
        value = sum_quantity.get('quantity__sum')
        total_quantity = value + quantity
        print(f"Total quantity for tracker detail product {tracker_detail_product.id}: {total_quantity}")
        if total_quantity > tracker_detail_product.available_quantity:
            raise QuantityExceeded()
        
        return attrs

    def _validate_direct_product(self, attrs, quantity):
        """Validación para productos directos (nueva lógica)"""
        product = attrs.get('product')
        distributor_center = attrs.get('distributor_center')
        expiration_date = attrs.get('expiration_date')
        
        if not distributor_center:
            raise serializers.ValidationError("distributor_center es requerido para productos directos")
        
        if not expiration_date:
            raise serializers.ValidationError("expiration_date es requerido para productos directos")
        
        # PRODUCTOS DIRECTOS NO TIENEN LÍMITE DE INVENTARIO
        # Solo validamos que los campos requeridos estén presentes
        if quantity <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        
        return attrs

    # cuando se registra la cantidad disponible es la misma que la cantidad
    def create(self, validated_data):
        validated_data['quantity_available'] = validated_data.get('quantity')
        instance = super(OrderDetailSerializer, self).create(validated_data)
        
        # PRODUCTOS DIRECTOS NO REQUIEREN RESERVA DE INVENTARIO
        # Solo los productos con tracker_detail_product tienen control de inventario automático
        
        return instance

    # cuando se actualiza la cantidad disponible es la misma que la cantidad
    def update(self, instance, validated_data):
        new_quantity = validated_data.get('quantity')
        validated_data['quantity_available'] = new_quantity
        
        # PRODUCTOS DIRECTOS NO REQUIEREN AJUSTE DE RESERVAS DE INVENTARIO
        # Solo los productos con tracker_detail_product tienen control de inventario automático
        
        return super(OrderDetailSerializer, self).update(instance, validated_data)
    class Meta:
        model = OrderDetailModel
        fields = '__all__'
        read_only_fields = ('quantity_available',)


# Serializer de ordenes de salida
class OutOrderSerializer(serializers.ModelSerializer):
    document = None
    class Meta:
        model = OutOrderModel
        exclude = ('document',)

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


