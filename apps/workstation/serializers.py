"""Serializers del módulo Workstation (modelo de bloques)."""
from datetime import date

from django.db.models import Q
from rest_framework import serializers

from .models import (
    ProhibitionCatalog,
    RiskCatalog,
    Workstation,
    WorkstationBlock,
    WorkstationDocument,
    WorkstationImage,
)


class RiskCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskCatalog
        fields = ['id', 'code', 'name', 'icon_name', 'is_active']


class ProhibitionCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProhibitionCatalog
        fields = ['id', 'code', 'name', 'icon_name', 'is_active']


def _kpi_targets_by_code(metric_codes: list[str], distributor_center_id: int | None):
    """Devuelve un dict {code: KPITargetModel} para los KPIs vigentes del CD."""
    if not metric_codes:
        return {}
    from apps.truck_cycle.models.catalogs import KPITargetModel
    today = date.today()
    qs = (
        KPITargetModel.objects
        .filter(
            metric_type__code__in=metric_codes,
            metric_type__is_active=True,
            effective_from__lte=today,
        )
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
        .select_related('metric_type')
    )
    if distributor_center_id:
        qs = qs.filter(distributor_center_id=distributor_center_id)
    return {kpi.metric_type.code: kpi for kpi in qs}


def expand_triggers_config(config: dict, distributor_center_id: int | None) -> dict:
    """
    Para bloques TRIGGERS: si `config.metric_codes` está poblado, expande con
    los valores vigentes de `KPITargetModel` para el CD. El frontend recibe
    `items` listo para renderizar. Si no hay `metric_codes`, se respeta el
    `items` legacy.
    """
    metric_codes = config.get('metric_codes') or []
    if not metric_codes:
        return config

    by_code = _kpi_targets_by_code(metric_codes, distributor_center_id)
    items = []
    for code in metric_codes:
        kpi = by_code.get(code)
        if not kpi:
            continue
        items.append({
            'metric_code': code,
            'indicator': kpi.metric_type.name,
            'meta': str(kpi.target_value),
            'disparador': str(kpi.warning_threshold) if kpi.warning_threshold is not None else '',
            'unit': kpi.unit or kpi.metric_type.unit or '',
            'direction': kpi.direction,
        })
    return {**config, 'items': items}


def expand_sic_chart_config(config: dict, distributor_center_id: int | None) -> dict:
    """
    Para bloques SIC_CHART: expande `config.metric_codes` con la configuración
    de KpiTarget vigente. Cada KPI termina con label, goal_min (target_value),
    yellow_min (warning_threshold) y direction — los mismos valores que la
    Carta SIC usa para pintar las zonas verde/amarillo/rojo.
    """
    metric_codes = config.get('metric_codes') or []
    if not metric_codes:
        return config

    by_code = _kpi_targets_by_code(metric_codes, distributor_center_id)
    kpis = []
    for code in metric_codes:
        kpi = by_code.get(code)
        if not kpi:
            continue
        kpis.append({
            'metric_code': code,
            'label': kpi.metric_type.name,
            'goal_min': float(kpi.target_value),
            'yellow_min': float(kpi.warning_threshold) if kpi.warning_threshold is not None else None,
            'unit': kpi.unit or kpi.metric_type.unit or '',
            'direction': kpi.direction,
        })
    return {**config, 'kpis': kpis}


class WorkstationBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkstationBlock
        fields = [
            'id', 'workstation', 'type', 'config',
            'grid_x', 'grid_y', 'grid_w', 'grid_h',
            'is_active', 'created_at',
        ]
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Expansión server-side: TRIGGERS y SIC_CHART comparten la misma fuente
        # (KPITargetModel del CD). El frontend recibe los valores listos.
        dc_id = instance.workstation.distributor_center_id
        if instance.type == WorkstationBlock.TYPE_TRIGGERS:
            data['config'] = expand_triggers_config(instance.config or {}, dc_id)
        elif instance.type == WorkstationBlock.TYPE_SIC_CHART:
            data['config'] = expand_sic_chart_config(instance.config or {}, dc_id)
        return data


class WorkstationDocumentSerializer(serializers.ModelSerializer):
    qr_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkstationDocument
        fields = [
            'id', 'workstation', 'doc_type', 'name', 'file', 'qr_token',
            'qr_url', 'is_active', 'created_at',
        ]
        read_only_fields = ['qr_token', 'created_at']

    def get_qr_url(self, obj):
        return f'/wd/{obj.qr_token}'


class WorkstationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkstationImage
        fields = ['id', 'workstation', 'name', 'file', 'alt', 'created_at']
        read_only_fields = ['created_at']


class WorkstationSerializer(serializers.ModelSerializer):
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    blocks = WorkstationBlockSerializer(many=True, read_only=True)
    documents = WorkstationDocumentSerializer(many=True, read_only=True)
    images = WorkstationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Workstation
        fields = [
            'id', 'distributor_center', 'distributor_center_name',
            'role', 'role_display', 'name', 'is_active', 'created_at',
            'blocks', 'documents', 'images',
        ]
        read_only_fields = ['created_at']

    def validate(self, attrs):
        dc = attrs.get('distributor_center') or getattr(self.instance, 'distributor_center', None)
        role = attrs.get('role') or getattr(self.instance, 'role', None)
        qs = Workstation.objects.filter(distributor_center=dc, role=role)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe una estación para este Centro de Distribución y rol.'
            )
        return attrs


class WorkstationListSerializer(serializers.ModelSerializer):
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    blocks_count = serializers.IntegerField(read_only=True, source='blocks.count')
    documents_count = serializers.IntegerField(read_only=True, source='documents.count')

    class Meta:
        model = Workstation
        fields = [
            'id', 'distributor_center', 'distributor_center_name',
            'role', 'role_display', 'name', 'is_active', 'created_at',
            'blocks_count', 'documents_count',
        ]


class BulkBlocksPayloadSerializer(serializers.Serializer):
    """Para reemplazar atómicamente todos los bloques tras un drag/resize masivo."""
    blocks = serializers.ListField(child=serializers.DictField())
