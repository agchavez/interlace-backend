"""
Serializers para el nuevo sistema de evaluaciones con métricas escalables
"""
from rest_framework import serializers
from ..models.performance_new import (
    PerformanceMetricType,
    PerformanceEvaluation,
    EvaluationMetricValue
)
from ..models.personnel import PersonnelProfile


class PerformanceMetricTypeSerializer(serializers.ModelSerializer):
    """Serializer completo para tipos de métricas"""
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = PerformanceMetricType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate(self, data):
        """Validaciones personalizadas"""
        # Validar que min_value < max_value
        if data.get('min_value') is not None and data.get('max_value') is not None:
            if data['min_value'] >= data['max_value']:
                raise serializers.ValidationError({
                    'max_value': 'El valor máximo debe ser mayor que el valor mínimo'
                })

        # Validar peso
        if data.get('weight', 0) < 0 or data.get('weight', 0) > 100:
            raise serializers.ValidationError({
                'weight': 'El peso debe estar entre 0 y 100'
            })

        return data


class PerformanceMetricTypeListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    applicable_positions_count = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceMetricType
        fields = [
            'id', 'name', 'code', 'metric_type', 'metric_type_display',
            'unit', 'weight', 'is_required', 'is_active', 'display_order',
            'applicable_positions_count'
        ]

    def get_applicable_positions_count(self, obj):
        """Cuenta de posiciones aplicables"""
        return len(obj.applicable_position_types) if obj.applicable_position_types else 0


class EvaluationMetricValueSerializer(serializers.ModelSerializer):
    """Serializer para valores de métricas"""
    metric_name = serializers.CharField(source='metric_type.name', read_only=True)
    metric_type_code = serializers.CharField(source='metric_type.code', read_only=True)
    metric_type_type = serializers.CharField(source='metric_type.metric_type', read_only=True)
    metric_unit = serializers.CharField(source='metric_type.unit', read_only=True, allow_null=True)
    display_value = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationMetricValue
        fields = [
            'id', 'evaluation', 'metric_type', 'metric_name', 'metric_type_code',
            'metric_type_type', 'metric_unit', 'numeric_value', 'text_value',
            'boolean_value', 'comments', 'display_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_display_value(self, obj):
        """Valor formateado para mostrar"""
        return obj.get_display_value()

    def validate(self, data):
        """Validar que el valor corresponde al tipo de métrica"""
        metric_type = data.get('metric_type')

        if not metric_type:
            return data

        # Validar según tipo
        if metric_type.metric_type == PerformanceMetricType.NUMERIC:
            if data.get('numeric_value') is None:
                raise serializers.ValidationError({
                    'numeric_value': 'Este campo es requerido para métricas numéricas'
                })
            # Validar rangos
            if metric_type.min_value is not None and data['numeric_value'] < metric_type.min_value:
                raise serializers.ValidationError({
                    'numeric_value': f'El valor debe ser mayor o igual a {metric_type.min_value}'
                })
            if metric_type.max_value is not None and data['numeric_value'] > metric_type.max_value:
                raise serializers.ValidationError({
                    'numeric_value': f'El valor debe ser menor o igual a {metric_type.max_value}'
                })

        elif metric_type.metric_type == PerformanceMetricType.RATING:
            if data.get('numeric_value') is None:
                raise serializers.ValidationError({
                    'numeric_value': 'Este campo es requerido para métricas de calificación'
                })
            if data['numeric_value'] < 1 or data['numeric_value'] > 5:
                raise serializers.ValidationError({
                    'numeric_value': 'La calificación debe estar entre 1 y 5'
                })

        elif metric_type.metric_type == PerformanceMetricType.PERCENTAGE:
            if data.get('numeric_value') is None:
                raise serializers.ValidationError({
                    'numeric_value': 'Este campo es requerido para métricas de porcentaje'
                })
            if data['numeric_value'] < 0 or data['numeric_value'] > 100:
                raise serializers.ValidationError({
                    'numeric_value': 'El porcentaje debe estar entre 0 y 100'
                })

        elif metric_type.metric_type == PerformanceMetricType.BOOLEAN:
            if data.get('boolean_value') is None:
                raise serializers.ValidationError({
                    'boolean_value': 'Este campo es requerido para métricas booleanas'
                })

        elif metric_type.metric_type == PerformanceMetricType.TEXT:
            if not data.get('text_value'):
                raise serializers.ValidationError({
                    'text_value': 'Este campo es requerido para métricas de texto'
                })

        return data


class PerformanceEvaluationSerializer(serializers.ModelSerializer):
    """Serializer completo para evaluaciones"""
    personnel_name = serializers.CharField(source='personnel.full_name', read_only=True)
    personnel_code = serializers.CharField(source='personnel.employee_code', read_only=True)
    personnel_position = serializers.CharField(source='personnel.position', read_only=True)
    evaluated_by_name = serializers.CharField(source='evaluated_by.full_name', read_only=True, allow_null=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    metric_values = EvaluationMetricValueSerializer(many=True, read_only=True)

    class Meta:
        model = PerformanceEvaluation
        fields = '__all__'
        read_only_fields = ['id', 'overall_score', 'created_at', 'updated_at', 'submitted_at']

    def validate(self, data):
        """Validar evaluación"""
        # Validar que la fecha de evaluación no sea futura
        from datetime import date
        if data.get('evaluation_date') and data['evaluation_date'] > date.today():
            raise serializers.ValidationError({
                'evaluation_date': 'La fecha de evaluación no puede ser futura'
            })

        return data


class PerformanceEvaluationListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    personnel_name = serializers.CharField(source='personnel.full_name', read_only=True)
    personnel_code = serializers.CharField(source='personnel.employee_code', read_only=True)
    position = serializers.CharField(source='personnel.position', read_only=True)
    evaluated_by_name = serializers.CharField(source='evaluated_by.full_name', read_only=True, allow_null=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    metrics_count = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceEvaluation
        fields = [
            'id', 'personnel', 'personnel_name', 'personnel_code', 'position',
            'evaluation_date', 'period', 'period_display', 'evaluated_by_name',
            'overall_score', 'is_draft', 'submitted_at', 'metrics_count'
        ]

    def get_metrics_count(self, obj):
        """Cantidad de métricas registradas"""
        return obj.metric_values.count()


class PerformanceEvaluationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear evaluación con métricas"""
    metric_values = EvaluationMetricValueSerializer(many=True, required=False)

    class Meta:
        model = PerformanceEvaluation
        fields = [
            'personnel', 'evaluation_date', 'period', 'evaluated_by',
            'comments', 'is_draft', 'metric_values'
        ]

    def create(self, validated_data):
        """Crear evaluación con métricas"""
        metric_values_data = validated_data.pop('metric_values', [])

        # Crear evaluación
        evaluation = PerformanceEvaluation.objects.create(**validated_data)

        # Crear valores de métricas
        for metric_value_data in metric_values_data:
            EvaluationMetricValue.objects.create(
                evaluation=evaluation,
                **metric_value_data
            )

        # Si no es borrador, calcular score y marcar como enviada
        if not evaluation.is_draft:
            from django.utils import timezone
            evaluation.submitted_at = timezone.now()
            evaluation.overall_score = evaluation.calculate_overall_score()
            evaluation.save()

        return evaluation

    def update(self, instance, validated_data):
        """Actualizar evaluación con métricas"""
        metric_values_data = validated_data.pop('metric_values', None)

        # Actualizar campos de la evaluación
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Si cambia de borrador a final, marcar como enviada
        if not instance.is_draft and instance.submitted_at is None:
            from django.utils import timezone
            instance.submitted_at = timezone.now()

        instance.save()

        # Actualizar métricas si se proporcionan
        if metric_values_data is not None:
            # Eliminar métricas existentes y crear nuevas
            instance.metric_values.all().delete()
            for metric_value_data in metric_values_data:
                EvaluationMetricValue.objects.create(
                    evaluation=instance,
                    **metric_value_data
                )

        return instance
