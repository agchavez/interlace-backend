"""
Serializers para registros médicos
"""
from rest_framework import serializers
from ..models.medical import MedicalRecord


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer de registros médicos"""
    record_type_display = serializers.CharField(
        source='get_record_type_display',
        read_only=True
    )
    is_active_incapacity = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    personnel_name = serializers.CharField(
        source='personnel.full_name',
        read_only=True
    )
    personnel_code = serializers.CharField(
        source='personnel.employee_code',
        read_only=True
    )

    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate(self, data):
        """Validaciones"""
        # Validar fechas
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'La fecha de fin no puede ser anterior a la fecha de inicio'
                })

        # Validar que incapacidades tengan fechas
        if data.get('record_type') == MedicalRecord.INCAPACITY:
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError({
                    'record_type': 'Las incapacidades requieren fecha de inicio y fin'
                })

        return data


class MedicalRecordListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    record_type_display = serializers.CharField(
        source='get_record_type_display',
        read_only=True
    )
    personnel_name = serializers.CharField(
        source='personnel.full_name',
        read_only=True
    )

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'personnel', 'personnel_name', 'record_type',
            'record_type_display', 'record_date', 'description',
            'start_date', 'end_date', 'is_confidential'
        ]
        read_only_fields = fields
