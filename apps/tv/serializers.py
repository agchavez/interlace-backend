from rest_framework import serializers

from .models import TvSession


class TvSessionPublicSerializer(serializers.ModelSerializer):
    """Lo que ve la TV durante el pareo (no incluye el token)."""
    class Meta:
        model = TvSession
        fields = ['code', 'status', 'expires_at', 'dashboard', 'label', 'config']
        read_only_fields = fields


class TvSessionPairedSerializer(serializers.ModelSerializer):
    """Incluye el access_token — solo se devuelve tras autenticar como TV."""
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)

    class Meta:
        model = TvSession
        fields = [
            'code', 'status', 'expires_at', 'access_token',
            'dashboard', 'label', 'config',
            'distributor_center', 'distributor_center_name',
        ]
        read_only_fields = fields


class TvSessionAdminSerializer(serializers.ModelSerializer):
    """Vista de admin — lista de TVs activas por CD."""
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    paired_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TvSession
        fields = [
            'id', 'code', 'status', 'label',
            'created_at', 'paired_at', 'expires_at', 'last_seen_at',
            'dashboard', 'distributor_center', 'distributor_center_name',
            'paired_by', 'paired_by_name', 'config',
            'user_agent', 'ip_address',
        ]
        read_only_fields = fields

    def get_paired_by_name(self, obj):
        if not obj.paired_by:
            return None
        return obj.paired_by.get_full_name() or obj.paired_by.username


class TvPairRequestSerializer(serializers.Serializer):
    """Payload del endpoint POST /tv/sessions/<code>/pair/."""
    distributor_center = serializers.IntegerField()
    dashboard = serializers.ChoiceField(
        choices=[c[0] for c in TvSession.DASHBOARD_CHOICES],
        default='WORKSTATION',
    )
    label = serializers.CharField(max_length=80, required=False, allow_blank=True, default='')
    ttl_days = serializers.IntegerField(required=False, min_value=1, max_value=30, default=7)
    config = serializers.JSONField(required=False, default=dict)
