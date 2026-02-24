"""
Serializers para PermitHourDetail
"""
from rest_framework import serializers
from ..models import PermitHourDetail


class PermitHourDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para PermitHourDetail"""
    reason_type_display = serializers.CharField(source='get_reason_type_display', read_only=True)
    actual_hours_used = serializers.DecimalField(
        max_digits=4, decimal_places=2, read_only=True
    )

    class Meta:
        model = PermitHourDetail
        fields = [
            'id',
            'reason_type', 'reason_type_display',
            'reason_description',
            'hours_requested',
            'exit_time', 'expected_return_time',
            'actual_exit_time', 'actual_return_time',
            'actual_hours_used',
            'with_pay',
        ]
        read_only_fields = ['id', 'reason_type_display', 'actual_hours_used']


class PermitHourCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear PermitHourDetail"""

    class Meta:
        model = PermitHourDetail
        fields = [
            'reason_type',
            'reason_description',
            'hours_requested',
            'exit_time',
            'expected_return_time',
            'with_pay',
        ]

    def validate(self, data):
        """Validaciones específicas para permiso por hora"""
        exit_time = data.get('exit_time')
        expected_return_time = data.get('expected_return_time')

        if exit_time and expected_return_time:
            # Calcular horas entre salida y retorno
            from datetime import datetime, timedelta
            exit_dt = datetime.combine(datetime.today(), exit_time)
            return_dt = datetime.combine(datetime.today(), expected_return_time)

            # Si retorno es antes que salida, asumir día siguiente
            if return_dt <= exit_dt:
                return_dt += timedelta(days=1)

            diff_hours = (return_dt - exit_dt).total_seconds() / 3600

            # Validar que las horas solicitadas coincidan aproximadamente
            hours_requested = float(data.get('hours_requested', 0))
            if abs(diff_hours - hours_requested) > 0.5:
                raise serializers.ValidationError({
                    'hours_requested': f'Las horas solicitadas ({hours_requested}) no coinciden con el rango de horas ({diff_hours:.2f}h).'
                })

        return data
