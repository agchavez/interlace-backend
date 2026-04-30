"""Views del módulo Workstation."""
import mimetypes

from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ProhibitionCatalog,
    RiskCatalog,
    Workstation,
    WorkstationBlock,
    WorkstationDocument,
    WorkstationImage,
)
from .permissions import IsAdmin, IsAdminOrCDChief
from .serializers import (
    ProhibitionCatalogSerializer,
    RiskCatalogSerializer,
    WorkstationBlockSerializer,
    WorkstationDocumentSerializer,
    WorkstationImageSerializer,
    WorkstationListSerializer,
    WorkstationSerializer,
)
from .templates import apply_default_template


# ────────── Mapping dashboard string → role ──────────
DASHBOARD_TO_ROLE = {
    'WORKSTATION_PICKING': Workstation.ROLE_PICKING,
    'WORKSTATION_PICKER':  Workstation.ROLE_PICKER,
    'WORKSTATION_COUNTER': Workstation.ROLE_COUNTER,
    'WORKSTATION_YARD':    Workstation.ROLE_YARD,
    'WORKSTATION_REPACK':  Workstation.ROLE_REPACK,
}


def get_workstation_for_tv(dashboard: str, distributor_center_id: int | None) -> Workstation | None:
    """Resuelve el Workstation correspondiente a una sesión TV."""
    if not distributor_center_id:
        return None
    role = DASHBOARD_TO_ROLE.get(dashboard)
    if not role:
        return None
    return (
        Workstation.objects
        .filter(distributor_center_id=distributor_center_id, role=role, is_active=True)
        .prefetch_related('blocks', 'documents', 'images')
        .first()
    )


# ────────── Catálogos master (admin escritura) ──────────

class RiskCatalogViewSet(viewsets.ModelViewSet):
    queryset = RiskCatalog.objects.all()
    serializer_class = RiskCatalogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class ProhibitionCatalogViewSet(viewsets.ModelViewSet):
    queryset = ProhibitionCatalog.objects.all()
    serializer_class = ProhibitionCatalogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


# ────────── Workstation ──────────

class WorkstationViewSet(viewsets.ModelViewSet):
    queryset = (
        Workstation.objects
        .select_related('distributor_center')
        .prefetch_related('blocks', 'documents', 'images')
        .all()
    )
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCDChief]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['distributor_center', 'role', 'is_active']
    search_fields = ['name', 'distributor_center__name']

    def get_serializer_class(self):
        if self.action == 'list':
            return WorkstationListSerializer
        return WorkstationSerializer

    def perform_create(self, serializer):
        """Al crear una estación, aplicar el template default según el rol."""
        ws = serializer.save()
        apply_default_template(ws)

    @action(detail=False, methods=['post'], url_path='ensure-for-role')
    def ensure_for_role(self, request):
        """Devuelve (o crea si no existe) la Workstation para un (CD, role).

        Idempotente — útil para el tab "Estaciones de Trabajo" que crea cards
        on-demand sin chocar con la unique constraint si la WS ya existía pero
        no estaba en la lista cargada por caché o paginación.

        Body: { distributor_center: int, role: str }
        """
        dc_id = request.data.get('distributor_center')
        role = request.data.get('role')
        if not dc_id or not role:
            return Response(
                {'error': 'distributor_center y role son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ws, created = Workstation.objects.get_or_create(
            distributor_center_id=dc_id,
            role=role,
            defaults={'name': '', 'is_active': True},
        )
        if created:
            apply_default_template(ws)
        return Response(WorkstationSerializer(ws).data, status=200 if not created else 201)

    @action(detail=True, methods=['post'], url_path='set_blocks')
    def set_blocks(self, request, pk=None):
        """
        Reemplaza atómicamente la lista completa de bloques de la estación.
        Body: { "blocks": [ { type, config, grid_x, grid_y, grid_w, grid_h, is_active }, ... ] }
        """
        ws = self.get_object()
        items = request.data.get('blocks') or []
        with transaction.atomic():
            WorkstationBlock.objects.filter(workstation=ws).delete()
            bulk = []
            for item in items:
                bulk.append(WorkstationBlock(
                    workstation=ws,
                    type=item.get('type', WorkstationBlock.TYPE_TEXT),
                    config=item.get('config') or {},
                    grid_x=int(item.get('grid_x', 0)),
                    grid_y=int(item.get('grid_y', 0)),
                    grid_w=int(item.get('grid_w', 4)),
                    grid_h=int(item.get('grid_h', 3)),
                    is_active=bool(item.get('is_active', True)),
                ))
            WorkstationBlock.objects.bulk_create(bulk)
        return Response(WorkstationSerializer(ws).data)

    @action(detail=True, methods=['post'], url_path='apply_template')
    def apply_template(self, request, pk=None):
        """Re-aplica el template default del rol (borra los bloques actuales)."""
        ws = self.get_object()
        with transaction.atomic():
            WorkstationBlock.objects.filter(workstation=ws).delete()
            apply_default_template(ws)
        return Response(WorkstationSerializer(ws).data)

    @action(detail=True, methods=['get'], url_path='available_kpis')
    def available_kpis(self, request, pk=None):
        """
        Lista los KPIs (PerformanceMetricType) que tienen KPITargetModel
        vigente en el CD del workstation. Lo usa el drawer para que el usuario
        elija qué disparadores mostrar en el bloque TRIGGERS.

        Respuesta: { items: [...], diagnostics: {...} }
        El diagnostics ayuda al usuario a entender por qué ve 0 disponibles
        cuando el CD sí tiene KPI Targets.
        """
        from datetime import date as _date
        from django.db.models import Q
        from apps.truck_cycle.models.catalogs import KPITargetModel

        ws = self.get_object()
        today = _date.today()

        all_targets = KPITargetModel.objects.filter(
            distributor_center_id=ws.distributor_center_id,
        ).select_related('metric_type')

        total = all_targets.count()
        legacy = all_targets.filter(metric_type__isnull=True).count()
        with_metric = all_targets.filter(metric_type__isnull=False).count()
        inactive_metric = all_targets.filter(
            metric_type__isnull=False, metric_type__is_active=False,
        ).count()
        not_yet_effective = all_targets.filter(
            metric_type__isnull=False, metric_type__is_active=True,
            effective_from__gt=today,
        ).count()
        expired = all_targets.filter(
            metric_type__isnull=False, metric_type__is_active=True,
            effective_to__isnull=False, effective_to__lt=today,
        ).count()

        qs = (
            all_targets
            .filter(
                metric_type__isnull=False,
                metric_type__is_active=True,
                effective_from__lte=today,
            )
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
        )
        items = []
        seen = set()
        for kpi in qs:
            code = kpi.metric_type.code
            if code in seen:
                continue
            seen.add(code)
            items.append({
                'code': code,
                'name': kpi.metric_type.name,
                'meta': str(kpi.target_value),
                'disparador': str(kpi.warning_threshold) if kpi.warning_threshold is not None else '',
                'unit': kpi.unit or kpi.metric_type.unit or '',
                'direction': kpi.direction,
            })

        return Response({
            'items': items,
            'diagnostics': {
                'distributor_center_id': ws.distributor_center_id,
                'total_targets': total,
                'legacy_targets': legacy,
                'targets_with_metric': with_metric,
                'inactive_metric_type': inactive_metric,
                'not_yet_effective': not_yet_effective,
                'expired': expired,
                'today': str(today),
            },
        })


# ────────── Bloques ──────────

class WorkstationBlockViewSet(viewsets.ModelViewSet):
    queryset = WorkstationBlock.objects.select_related('workstation').all()
    serializer_class = WorkstationBlockSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCDChief]
    filterset_fields = ['workstation', 'type', 'is_active']


# ────────── Documentos ──────────

class WorkstationDocumentViewSet(viewsets.ModelViewSet):
    queryset = WorkstationDocument.objects.select_related('workstation').all()
    serializer_class = WorkstationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCDChief]
    filterset_fields = ['workstation', 'doc_type', 'is_active']


class WorkstationImageViewSet(viewsets.ModelViewSet):
    queryset = WorkstationImage.objects.select_related('workstation').all()
    serializer_class = WorkstationImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCDChief]
    filterset_fields = ['workstation']


# ────────── Descarga del PDF vía qr_token ──────────

class WorkstationDocumentDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, qr_token: str):
        doc = get_object_or_404(
            WorkstationDocument.objects.select_related('workstation'),
            qr_token=qr_token, is_active=True,
        )
        if not doc.file:
            raise Http404('Sin archivo.')
        content_type, _ = mimetypes.guess_type(doc.file.name)
        content_type = content_type or 'application/pdf'
        response = FileResponse(doc.file.open('rb'), content_type=content_type)
        safe_name = doc.name.replace('"', "'")
        response['Content-Disposition'] = f'inline; filename="{safe_name}.pdf"'
        return response


class WorkstationDocumentMetaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, qr_token: str):
        doc = get_object_or_404(
            WorkstationDocument.objects.select_related('workstation__distributor_center'),
            qr_token=qr_token, is_active=True,
        )
        return Response({
            'id': doc.id,
            'name': doc.name,
            'doc_type': doc.doc_type,
            'doc_type_display': doc.get_doc_type_display(),
            'workstation_id': doc.workstation_id,
            'workstation_label': str(doc.workstation),
            'distributor_center': doc.workstation.distributor_center.name,
            'role': doc.workstation.role,
            'role_display': doc.workstation.get_role_display(),
        })
