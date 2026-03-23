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
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = PautaAssignmentModel
        fields = '__all__'


class PautaTimestampSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(
        source='get_event_type_display', read_only=True
    )

    class Meta:
        model = PautaTimestampModel
        fields = '__all__'


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

    class Meta:
        model = InconsistencyModel
        fields = '__all__'

    def validate(self, data):
        """Auto-calcular diferencia basada en cantidad esperada vs real"""
        expected = data.get('expected_quantity', 0)
        actual = data.get('actual_quantity', 0)
        data['difference'] = actual - expected
        return data


class PautaPhotoSerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)

    class Meta:
        model = PautaPhotoModel
        fields = '__all__'


class CheckoutValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutValidationModel
        fields = '__all__'


class PalletTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalletTicketModel
        fields = '__all__'
