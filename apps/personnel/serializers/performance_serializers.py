"""
Serializers para métricas de desempeño
"""
from rest_framework import serializers
from ..models.performance import PerformanceMetric


class PerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer de métricas de desempeño"""
    period_display = serializers.CharField(
        source='get_period_display',
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
    evaluated_by_name = serializers.CharField(
        source='evaluated_by.full_name',
        read_only=True,
        allow_null=True
    )
    performance_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = PerformanceMetric
        fields = '__all__'
        read_only_fields = [
            'id', 'productivity_rate', 'performance_score',
            'created_at', 'updated_at'
        ]

    def validate(self, data):
        """Validaciones"""
        # Validar que evaluated_by sea supervisor o superior
        if data.get('evaluated_by'):
            if not data['evaluated_by'].can_approve_tokens_level_1():
                raise serializers.ValidationError({
                    'evaluated_by': 'Solo supervisores o superiores pueden evaluar'
                })

        # Validar supervisor_rating entre 1 y 5
        if data.get('supervisor_rating'):
            if not 1 <= data['supervisor_rating'] <= 5:
                raise serializers.ValidationError({
                    'supervisor_rating': 'La calificación debe estar entre 1 y 5'
                })

        return data


class PerformanceMetricListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    period_display = serializers.CharField(
        source='get_period_display',
        read_only=True
    )

    class Meta:
        model = PerformanceMetric
        fields = [
            'id', 'personnel', 'metric_date', 'period', 'period_display',
            'pallets_moved', 'hours_worked', 'productivity_rate',
            'errors_count', 'supervisor_rating'
        ]
        read_only_fields = fields
