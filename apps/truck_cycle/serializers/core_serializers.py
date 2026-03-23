"""
Serializers para modelos principales del ciclo del camión
"""
from rest_framework import serializers
from apps.truck_cycle.models.core import (
    PalletComplexUploadModel,
    PautaModel,
    PautaProductDetailModel,
    PautaDeliveryDetailModel,
)
from apps.truck_cycle.serializers.operational_serializers import (
    PautaAssignmentSerializer,
    PautaTimestampSerializer,
    InconsistencySerializer,
    PautaPhotoSerializer,
    CheckoutValidationSerializer,
    PalletTicketSerializer,
)


class PalletComplexUploadSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name', read_only=True
    )

    class Meta:
        model = PalletComplexUploadModel
        fields = '__all__'


class PalletComplexUploadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalletComplexUploadModel
        fields = ['file', 'file_name', 'distributor_center']


class PautaProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PautaProductDetailModel
        fields = '__all__'


class PautaDeliveryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PautaDeliveryDetailModel
        fields = '__all__'


class PautaListSerializer(serializers.ModelSerializer):
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PautaModel
        fields = [
            'id',
            'transport_number',
            'trip_number',
            'route_code',
            'total_boxes',
            'total_skus',
            'total_pallets',
            'complexity_score',
            'status',
            'status_display',
            'operational_date',
            'is_reload',
            'truck',
            'truck_plate',
            'distributor_center',
            'created_at',
        ]


class PautaBayAssignmentNestedSerializer(serializers.Serializer):
    """Serializer ligero para bay_assignment anidado en PautaDetail"""
    id = serializers.IntegerField()
    bay_id = serializers.IntegerField()
    bay_code = serializers.CharField(source='bay.code')
    bay_name = serializers.CharField(source='bay.name')
    assigned_at = serializers.DateTimeField()
    released_at = serializers.DateTimeField()


class PautaDetailSerializer(serializers.ModelSerializer):
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    product_details = PautaProductDetailSerializer(many=True, read_only=True)
    delivery_details = PautaDeliveryDetailSerializer(many=True, read_only=True)
    assignments = PautaAssignmentSerializer(many=True, read_only=True)
    timestamps = PautaTimestampSerializer(many=True, read_only=True)
    bay_assignment = PautaBayAssignmentNestedSerializer(read_only=True)
    inconsistencies = InconsistencySerializer(many=True, read_only=True)
    photos = PautaPhotoSerializer(many=True, read_only=True)
    checkout_validation = CheckoutValidationSerializer(read_only=True)
    pallet_tickets = PalletTicketSerializer(many=True, read_only=True)

    class Meta:
        model = PautaModel
        fields = '__all__'
