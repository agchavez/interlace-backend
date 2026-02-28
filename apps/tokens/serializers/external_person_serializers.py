"""
Serializers para ExternalPerson (personas externas/proveedores)
"""
from rest_framework import serializers
from ..models import ExternalPerson


class ExternalPersonSerializer(serializers.ModelSerializer):
    """Serializer completo para ExternalPerson"""

    class Meta:
        model = ExternalPerson
        fields = [
            'id',
            'name',
            'company',
            'identification',
            'phone',
            'email',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExternalPersonListSerializer(serializers.ModelSerializer):
    """Serializer reducido para listados"""

    class Meta:
        model = ExternalPerson
        fields = [
            'id',
            'name',
            'company',
            'identification',
            'phone',
            'is_active',
        ]
        read_only_fields = ['id']


class ExternalPersonCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear ExternalPerson"""

    class Meta:
        model = ExternalPerson
        fields = [
            'name',
            'company',
            'identification',
            'phone',
            'email',
            'notes',
        ]

    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres")
        return value.strip()


class ExternalPersonBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para referencias en otros serializers"""

    class Meta:
        model = ExternalPerson
        fields = ['id', 'name', 'company', 'identification', 'phone']
        read_only_fields = ['id', 'name', 'company', 'identification', 'phone']
