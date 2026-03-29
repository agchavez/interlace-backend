"""
ViewSets para modelos operativos del ciclo del camión
"""
import uuid

from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.truck_cycle.models.operational import (
    InconsistencyModel,
    PautaPhotoModel,
    PalletTicketModel,
)
from apps.truck_cycle.serializers.operational_serializers import (
    InconsistencySerializer,
    PautaPhotoSerializer,
    PalletTicketSerializer,
)


def get_user_distributor_center(request):
    """Obtener el centro de distribución del usuario actual"""
    try:
        return request.user.personnel_profile.primary_distributor_center
    except Exception:
        return None


class InconsistencyViewSet(viewsets.ModelViewSet):
    """Gestión de inconsistencias"""
    serializer_class = InconsistencySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return InconsistencyModel.objects.filter(
                pauta__distributor_center=dc
            )
        return InconsistencyModel.objects.none()

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class PautaPhotoViewSet(viewsets.ModelViewSet):
    """Gestión de fotos de pautas"""
    serializer_class = PautaPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return PautaPhotoModel.objects.filter(
                pauta__distributor_center=dc
            )
        return PautaPhotoModel.objects.none()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class PalletTicketViewSet(viewsets.ModelViewSet):
    """Gestión de tickets de tarima"""
    serializer_class = PalletTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return PalletTicketModel.objects.filter(
                pauta__distributor_center=dc
            )
        return PalletTicketModel.objects.none()

    def perform_create(self, serializer):
        """Auto-generar QR code único al crear ticket"""
        qr_code = f"PLT-{uuid.uuid4().hex[:12].upper()}"
        serializer.save(qr_code=qr_code)

    @action(detail=True, methods=['post'])
    def scan(self, request, pk=None):
        """Marcar ticket como escaneado"""
        ticket = self.get_object()
        if ticket.scanned:
            return Response(
                {'error': 'Este ticket ya fue escaneado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ticket.scanned = True
        ticket.scanned_at = timezone.now()
        ticket.save(update_fields=['scanned', 'scanned_at'])
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate_for_pauta(self, request):
        """Generar tickets de pallet para una pauta completa"""
        from apps.truck_cycle.models.core import PautaModel
        pauta_id = request.data.get('pauta_id')
        if not pauta_id:
            return Response(
                {'error': 'pauta_id es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dc = get_user_distributor_center(request)
            pauta = PautaModel.objects.get(id=pauta_id, distributor_center=dc)
        except PautaModel.DoesNotExist:
            return Response(
                {'error': 'Pauta no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generar tickets basados en los productos de la pauta
        tickets_created = []
        ticket_num = 1
        for product in pauta.product_details.all():
            # Un ticket por pallet completo
            for _ in range(product.full_pallets):
                from apps.truck_cycle.models.catalogs import ProductCatalogModel
                catalog = ProductCatalogModel.objects.filter(
                    sku_code=product.material_code,
                    distributor_center=dc,
                ).first()
                boxes = catalog.boxes_per_pallet if catalog else product.total_boxes

                ticket = PalletTicketModel.objects.create(
                    ticket_number=f"{pauta.transport_number}-{ticket_num:03d}",
                    qr_code=f"PLT-{uuid.uuid4().hex[:12].upper()}",
                    is_full_pallet=True,
                    box_count=boxes,
                    pauta=pauta,
                )
                tickets_created.append(ticket.id)
                ticket_num += 1

            # Ticket para fracción si existe
            if product.fraction > 0:
                fraction_boxes = product.total_boxes - (product.full_pallets * (catalog.boxes_per_pallet if catalog else 0))
                if fraction_boxes > 0:
                    ticket = PalletTicketModel.objects.create(
                        ticket_number=f"{pauta.transport_number}-{ticket_num:03d}",
                        qr_code=f"PLT-{uuid.uuid4().hex[:12].upper()}",
                        is_full_pallet=False,
                        box_count=fraction_boxes,
                        pauta=pauta,
                    )
                    tickets_created.append(ticket.id)
                    ticket_num += 1

        return Response({
            'message': f'Se generaron {len(tickets_created)} tickets.',
            'ticket_ids': tickets_created,
            'pauta_id': pauta_id,
        })
