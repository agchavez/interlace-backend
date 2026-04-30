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
    truck_code = serializers.CharField(source='truck.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    last_status_change = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    bay_code = serializers.SerializerMethodField()
    bay_id = serializers.SerializerMethodField()
    # Campos extra para vistas ricas (workstation status detail, etc.)
    roles = serializers.SerializerMethodField()
    status_started_at = serializers.SerializerMethodField()
    inconsistencies_count = serializers.SerializerMethodField()
    photos_count = serializers.SerializerMethodField()
    assembled_fractions = serializers.IntegerField(read_only=True)
    dispatched_without_security = serializers.SerializerMethodField()

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
            'assembled_fractions',
            'status',
            'status_display',
            'operational_date',
            'is_reload',
            'reentered_at',
            'truck',
            'truck_plate',
            'truck_code',
            'distributor_center',
            'created_at',
            'last_status_change',
            'status_started_at',
            'assigned_to',
            'roles',
            'inconsistencies_count',
            'photos_count',
            'bay_code',
            'bay_id',
            'dispatched_without_security',
        ]

    def get_dispatched_without_security(self, obj):
        checkout = getattr(obj, 'checkout_validation', None)
        return bool(checkout and checkout.dispatched_without_security)

    def get_roles(self, obj):
        """Mapa role → {name, since} con la última asignación activa por rol."""
        snapshot = {}
        for a in obj.assignments.filter(is_active=True).select_related('personnel').order_by('-assigned_at'):
            if a.role in snapshot or not a.personnel:
                continue
            snapshot[a.role] = {
                'name': a.personnel.full_name,
                'role_display': a.get_role_display(),
                'since': a.assigned_at.isoformat(),
            }
        # Incluir checkout validators si aplica — útil para status CHECKOUT_*
        checkout = getattr(obj, 'checkout_validation', None)
        if checkout:
            if checkout.security_validator and 'SECURITY' not in snapshot:
                snapshot['SECURITY'] = {
                    'name': checkout.security_validator.full_name,
                    'role_display': 'Seguridad',
                    'since': checkout.security_validated_at.isoformat() if checkout.security_validated_at else None,
                }
            if checkout.ops_validator and 'OPERATIONS' not in snapshot:
                snapshot['OPERATIONS'] = {
                    'name': checkout.ops_validator.full_name,
                    'role_display': 'Operaciones',
                    'since': checkout.ops_validated_at.isoformat() if checkout.ops_validated_at else None,
                }
        return snapshot

    def get_status_started_at(self, obj):
        """Timestamp del evento que llevó al status actual (para medir cuánto lleva)."""
        # Mapa status → tipo de timestamp que lo inicia.
        STATUS_EVENT = {
            'PICKING_IN_PROGRESS': 'T0_PICKING_START',
            'PICKING_DONE':        'T1_PICKING_END',
            'MOVING_TO_BAY':       'T1A_YARD_START',
            'IN_BAY':              'T1B_YARD_END',
            'COUNTING':            'T5_COUNT_START',
            'COUNTED':             'T6_COUNT_END',
            'MOVING_TO_PARKING':   'T8A_YARD_RETURN_START',
            'PARKED':              'T8B_YARD_RETURN_END',
            'CHECKOUT_SECURITY':   'T7_CHECKOUT_SECURITY',
            'CHECKOUT_OPS':        'T8_CHECKOUT_OPS',
            'DISPATCHED':          'T9_DISPATCH',
            'IN_RELOAD_QUEUE':     'T10_ARRIVAL',
            'RETURN_PROCESSED':    'T13_RETURN_END',
            'IN_AUDIT':            'T14_AUDIT_START',
            'AUDIT_COMPLETE':      'T15_AUDIT_END',
            'CLOSED':              'T16_CLOSE',
        }
        target = STATUS_EVENT.get(obj.status)
        if target:
            ts = obj.timestamps.filter(event_type=target).order_by('-timestamp').first()
            if ts:
                return ts.timestamp.isoformat()
        # Fallback: último timestamp (o created_at si no hay).
        last = obj.timestamps.order_by('-timestamp').first()
        return last.timestamp.isoformat() if last else obj.created_at.isoformat()

    def get_inconsistencies_count(self, obj):
        return obj.inconsistencies.count()

    def get_photos_count(self, obj):
        return obj.photos.count()

    def get_last_status_change(self, obj):
        last = obj.timestamps.order_by('-timestamp').first()
        return last.timestamp if last else None

    def get_assigned_to(self, obj):
        # Para checkout: mostrar el validador correspondiente
        if obj.status in ('CHECKOUT_SECURITY', 'CHECKOUT_OPS', 'DISPATCHED'):
            checkout = getattr(obj, 'checkout_validation', None)
            if checkout:
                if obj.status == 'CHECKOUT_OPS' and checkout.ops_validator:
                    return {'name': checkout.ops_validator.full_name, 'role': 'Operaciones'}
                if checkout.security_validator:
                    return {'name': checkout.security_validator.full_name, 'role': 'Seguridad'}

        # Para picking/conteo/bahía: mostrar la asignación activa más relevante
        # Buscar por rol según el status actual
        STATUS_ROLE_MAP = {
            'PENDING_PICKING': 'PICKER', 'PICKING_ASSIGNED': 'PICKER',
            'PICKING_IN_PROGRESS': 'PICKER', 'PICKING_DONE': 'PICKER',
            'MOVING_TO_BAY': 'YARD_DRIVER',
            'IN_BAY': 'YARD_DRIVER',
            'PENDING_COUNT': 'COUNTER', 'COUNTING': 'COUNTER', 'COUNTED': 'COUNTER',
            'MOVING_TO_PARKING': 'YARD_DRIVER', 'PARKED': 'YARD_DRIVER',
        }
        preferred_role = STATUS_ROLE_MAP.get(obj.status)
        if preferred_role:
            assignment = obj.assignments.filter(
                is_active=True, role=preferred_role
            ).order_by('-assigned_at').first()
            if assignment:
                return {
                    'name': assignment.personnel.full_name if assignment.personnel else '',
                    'role': assignment.get_role_display(),
                }

        # Fallback: última asignación activa
        assignment = obj.assignments.filter(is_active=True).order_by('-assigned_at').first()
        if not assignment:
            return None
        return {
            'name': assignment.personnel.full_name if assignment.personnel else '',
            'role': assignment.get_role_display(),
        }

    def get_bay_code(self, obj):
        bay_assignment = getattr(obj, 'bay_assignment', None)
        if bay_assignment and not bay_assignment.released_at:
            return f'{bay_assignment.bay.code} - {bay_assignment.bay.name}'
        return None

    def get_bay_id(self, obj):
        bay_assignment = getattr(obj, 'bay_assignment', None)
        if bay_assignment and not bay_assignment.released_at:
            return bay_assignment.bay_id
        return None


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
    truck_code = serializers.CharField(source='truck.code', read_only=True)
    truck_primary_driver_id = serializers.IntegerField(source='truck.primary_driver_id', read_only=True)
    truck_primary_driver_name = serializers.CharField(source='truck.primary_driver.full_name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
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
