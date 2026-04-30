"""
Serializers para modelos operativos del ciclo del camión
"""
from rest_framework import serializers
from apps.truck_cycle.models.operational import (
    PautaAssignmentModel,
    PautaTimestampModel,
    PautaBayAssignmentModel,
    InconsistencyModel,
    PautaPhotoModel,
    CheckoutValidationModel,
    PalletTicketModel,
)


class PautaAssignmentSerializer(serializers.ModelSerializer):
    personnel_name = serializers.CharField(
        source='personnel.full_name', read_only=True
    )
    personnel_id = serializers.IntegerField(source='personnel.id', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PautaAssignmentModel
        fields = '__all__'

    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.get_full_name() or obj.assigned_by.username
        return ''


class PautaTimestampSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(
        source='get_event_type_display', read_only=True
    )
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PautaTimestampModel
        fields = '__all__'

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name() or obj.recorded_by.username
        return ''


class PautaBayAssignmentSerializer(serializers.ModelSerializer):
    bay_code = serializers.CharField(source='bay.code', read_only=True)
    bay_name = serializers.CharField(source='bay.name', read_only=True)

    class Meta:
        model = PautaBayAssignmentModel
        fields = '__all__'


class InconsistencySerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)
    type_display = serializers.CharField(
        source='get_inconsistency_type_display', read_only=True
    )
    reported_by_name = serializers.SerializerMethodField()

    class Meta:
        model = InconsistencyModel
        fields = '__all__'
        extra_kwargs = {
            'expected_quantity': {'required': False, 'default': 0},
        }

    # Mapa de signo por tipo: el contador solo registra una cantidad y el
    # tipo determina si suma o resta. CRUCE quedó deprecated — los registros
    # antiguos se siguen mostrando, pero el form no lo ofrece más.
    SIGN_BY_TYPE = {
        'FALTANTE': -1,
        'SOBRANTE': +1,
        'DANADO':   -1,
        'CRUCE':    -1,
    }

    def validate(self, data):
        """Auto-calcular diferencia basada en el tipo de inconsistencia."""
        actual = data.get('actual_quantity', 0)
        inc_type = data.get('inconsistency_type')
        sign = self.SIGN_BY_TYPE.get(inc_type, -1)
        data['expected_quantity'] = 0
        data['difference'] = sign * actual
        return data

    def get_reported_by_name(self, obj):
        if obj.reported_by:
            return obj.reported_by.get_full_name() or obj.reported_by.username
        return ''


class PautaPhotoSerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PautaPhotoModel
        fields = '__all__'

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return ''


class CheckoutValidationSerializer(serializers.ModelSerializer):
    security_validator_name = serializers.SerializerMethodField()
    ops_validator_name = serializers.SerializerMethodField()

    class Meta:
        model = CheckoutValidationModel
        fields = '__all__'

    def get_security_validator_name(self, obj):
        if obj.security_validator:
            return obj.security_validator.full_name
        return None

    def get_ops_validator_name(self, obj):
        if obj.ops_validator:
            return obj.ops_validator.full_name
        return None


class PalletTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalletTicketModel
        fields = '__all__'
