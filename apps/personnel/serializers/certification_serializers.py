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
    completed_by_name = serializers.CharField(
        source='completed_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    # Propiedades calculadas
    days_until_expiration = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    certificate_document_url = serializers.CharField(read_only=True, allow_null=True)
    signature_url = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Certification
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'renewal_notification_sent', 'renewal_notification_date',
            'signature', 'completion_notes', 'completed_at', 'completed_by',
            'non_completion_reason',
        ]

    def validate(self, data):
        """Validaciones"""
        # Validar fechas
        if data.get('expiration_date') and data.get('issue_date'):
            if data['expiration_date'] <= data['issue_date']:
                raise serializers.ValidationError({
                    'expiration_date': 'La fecha de vencimiento debe ser posterior a la fecha de emisión'
                })

        # Validar certificación duplicada (solo en creación, si hay número de certificación)
        if self.instance is None:
            cert_number = data.get('certification_number', '')
            if cert_number:
                existing = Certification.objects.filter(
                    personnel=data.get('personnel'),
                    certification_type=data.get('certification_type'),
                    certification_number=cert_number,
                ).exists()
                if existing:
                    raise serializers.ValidationError({
                        'certification_number': 'Ya existe una certificación con este número para este empleado'
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
    certificate_document_url = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Certification
        fields = [
            'id', 'personnel', 'personnel_name', 'personnel_code',
            'certification_type', 'certification_type_name',
            'certification_number', 'issuing_authority',
            'issue_date', 'expiration_date', 'is_valid', 'status', 'status_display',
            'days_until_expiration', 'certificate_document', 'certificate_document_url',
            'completed_at',
        ]
        read_only_fields = fields
