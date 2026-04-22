"""Serializers para PersonnelMetricSample."""
from rest_framework import serializers
from apps.personnel.models.metric_sample import PersonnelMetricSample


class PersonnelMetricSampleSerializer(serializers.ModelSerializer):
    metric_code = serializers.CharField(source='metric_type.code', read_only=True)
    metric_name = serializers.CharField(source='metric_type.name', read_only=True)
    metric_unit = serializers.CharField(source='metric_type.unit', read_only=True)
    personnel_name = serializers.CharField(source='personnel.full_name', read_only=True)
    personnel_code = serializers.CharField(source='personnel.employee_code', read_only=True)
    position_type = serializers.CharField(source='personnel.position_type', read_only=True)

    class Meta:
        model = PersonnelMetricSample
        fields = [
            'id',
            'personnel',
            'personnel_name',
            'personnel_code',
            'position_type',
            'metric_type',
            'metric_code',
            'metric_name',
            'metric_unit',
            'operational_date',
            'numeric_value',
            'source',
            'pauta_id',
            'context',
            'created_at',
        ]
        read_only_fields = fields
