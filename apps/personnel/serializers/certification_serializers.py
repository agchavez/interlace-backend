"""
Serializers para certificaciones
"""
from rest_framework import serializers
from ..models.certification import Certification, CertificationType


class CertificationTypeSerializer(serializers.ModelSerializer):
    """Serializer de tipos de certificación"""

    class Meta:
        model = CertificationType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CertificationSerializer(serializers.ModelSerializer):
    """Serializer de certificaciones"""
    certification_type_name = serializers.CharField(
        source='certification_type.name',
        read_only=True
    )
    personnel_name = serializers.CharField(
        source='personnel.full_name',
        read_only=True
    )
    personnel_code = serializers.CharField(
        source='personnel.employee_code',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    # Propiedades calculadas
    days_until_expiration = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    certificate_document_url = serializers.CharField(read_only=True)

    class Meta:
        model = Certification
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'renewal_notification_sent', 'renewal_notification_date'
        ]

    def validate(self, data):
        """Validaciones"""
        # Validar fechas
        if data.get('expiration_date') and data.get('issue_date'):
            if data['expiration_date'] <= data['issue_date']:
                raise serializers.ValidationError({
                    'expiration_date': 'La fecha de vencimiento debe ser posterior a la fecha de emisión'
                })

        # Validar certificación duplicada
        if self.instance is None:  # Solo en creación
            existing = Certification.objects.filter(
                personnel=data.get('personnel'),
                certification_type=data.get('certification_type'),
                is_valid=True
            ).exists()
            if existing:
                raise serializers.ValidationError({
                    'certification_type': 'Ya existe una certificación válida de este tipo para este empleado'
                })

        return data


class CertificationListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    certification_type_name = serializers.CharField(
        source='certification_type.name',
        read_only=True
    )
    personnel_name = serializers.CharField(
        source='personnel.full_name',
        read_only=True
    )
    personnel_code = serializers.CharField(
        source='personnel.employee_code',
        read_only=True
    )
    status_display = serializers.CharField(read_only=True)
    days_until_expiration = serializers.IntegerField(read_only=True)
    certificate_document_url = serializers.CharField(read_only=True)

    class Meta:
        model = Certification
        fields = [
            'id', 'personnel', 'personnel_name', 'personnel_code',
            'certification_type', 'certification_type_name',
            'certification_number', 'issuing_authority',
            'issue_date', 'expiration_date', 'is_valid', 'status_display',
            'days_until_expiration', 'certificate_document', 'certificate_document_url'
        ]
        read_only_fields = fields
