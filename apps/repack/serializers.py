from rest_framework import serializers

from .models import RepackSession, RepackEntry


class RepackEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RepackEntry
        fields = [
            'id', 'session', 'product', 'material_code', 'product_name',
            'box_count', 'expiration_date', 'notes', 'created_at',
        ]
        read_only_fields = ['created_at']


class RepackSessionListSerializer(serializers.ModelSerializer):
    personnel_name = serializers.CharField(source='personnel.full_name', read_only=True)
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_boxes = serializers.IntegerField(read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True)
    boxes_per_hour = serializers.FloatField(read_only=True)
    entries_count = serializers.SerializerMethodField()

    class Meta:
        model = RepackSession
        fields = [
            'id', 'personnel', 'personnel_name',
            'distributor_center', 'distributor_center_name',
            'operational_date', 'started_at', 'ended_at',
            'status', 'status_display', 'notes',
            'total_boxes', 'duration_seconds', 'boxes_per_hour',
            'entries_count', 'created_at',
        ]

    def get_entries_count(self, obj):
        return obj.entries.count()


class RepackSessionDetailSerializer(RepackSessionListSerializer):
    entries = RepackEntrySerializer(many=True, read_only=True)

    class Meta(RepackSessionListSerializer.Meta):
        fields = RepackSessionListSerializer.Meta.fields + ['entries']
