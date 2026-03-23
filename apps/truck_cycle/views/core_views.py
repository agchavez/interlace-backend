"""
ViewSets para modelos principales del ciclo del camión
"""
import io
from collections import defaultdict
from decimal import Decimal

from django.http import HttpResponse
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

import openpyxl

from apps.truck_cycle.models.catalogs import TruckModel, ProductCatalogModel
from apps.truck_cycle.models.core import (
    PalletComplexUploadModel,
    PautaModel,
    PautaProductDetailModel,
    PautaDeliveryDetailModel,
)
from apps.truck_cycle.models.operational import PautaTimestampModel, PautaAssignmentModel
from apps.truck_cycle.serializers.core_serializers import (
    PalletComplexUploadSerializer,
    PalletComplexUploadCreateSerializer,
    PautaListSerializer,
    PautaDetailSerializer,
)
from apps.truck_cycle.filters import PautaFilter


def get_user_distributor_center(request):
    """Obtener el centro de distribución del usuario actual"""
    try:
        return request.user.personnelprofile.primary_distributor_center
    except Exception:
        return None


# Mapa de transiciones válidas: estado_actual -> (nuevo_estado, evento_timestamp)
STATUS_TRANSITIONS = {
    'assign_picker': {
        'from': ['PENDING_PICKING'],
        'to': 'PICKING_ASSIGNED',
        'event': None,
    },
    'start_picking': {
        'from': ['PICKING_ASSIGNED'],
        'to': 'PICKING_IN_PROGRESS',
        'event': 'T0_PICKING_START',
    },
    'complete_picking': {
        'from': ['PICKING_IN_PROGRESS'],
        'to': 'PICKING_DONE',
        'event': 'T1_PICKING_END',
    },
    'assign_bay': {
        'from': ['PICKING_DONE'],
        'to': 'IN_BAY',
        'event': 'T2_BAY_ASSIGNED',
    },
    'complete_loading': {
        'from': ['IN_BAY'],
        'to': 'PENDING_COUNT',
        'event': 'T4_LOADING_END',
    },
    'assign_counter': {
        'from': ['PENDING_COUNT'],
        'to': 'COUNTING',
        'event': 'T5_COUNT_START',
    },
    'complete_count': {
        'from': ['COUNTING'],
        'to': 'COUNTED',
        'event': 'T6_COUNT_END',
    },
    'checkout_security': {
        'from': ['COUNTED', 'PENDING_CHECKOUT'],
        'to': 'CHECKOUT_SECURITY',
        'event': 'T7_CHECKOUT_SECURITY',
    },
    'checkout_ops': {
        'from': ['CHECKOUT_SECURITY'],
        'to': 'CHECKOUT_OPS',
        'event': 'T8_CHECKOUT_OPS',
    },
    'dispatch': {
        'from': ['CHECKOUT_OPS'],
        'to': 'DISPATCHED',
        'event': 'T9_DISPATCH',
    },
    'arrival': {
        'from': ['DISPATCHED'],
        'to': 'IN_RELOAD_QUEUE',
        'event': 'T10_ARRIVAL',
    },
    'process_return': {
        'from': ['PENDING_RETURN', 'IN_RELOAD_QUEUE'],
        'to': 'RETURN_PROCESSED',
        'event': 'T13_RETURN_END',
    },
    'start_audit': {
        'from': ['RETURN_PROCESSED', 'COUNTED'],
        'to': 'IN_AUDIT',
        'event': 'T14_AUDIT_START',
    },
    'complete_audit': {
        'from': ['IN_AUDIT'],
        'to': 'AUDIT_COMPLETE',
        'event': 'T15_AUDIT_END',
    },
    'close': {
        'from': ['AUDIT_COMPLETE', 'DISPATCHED', 'RETURN_PROCESSED'],
        'to': 'CLOSED',
        'event': 'T16_CLOSE',
    },
}


class PalletComplexUploadViewSet(viewsets.ModelViewSet):
    """Gestión de cargas masivas de pautas"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return PalletComplexUploadCreateSerializer
        return PalletComplexUploadSerializer

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return PalletComplexUploadModel.objects.filter(distributor_center=dc)
        return PalletComplexUploadModel.objects.none()

    @action(detail=False, methods=['get'])
    def template(self, request):
        """Descargar plantilla Excel vacía con las columnas esperadas"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pauta de Complejidad"
        columns = [
            'Transporte', 'Viaje', 'Ruta', 'Material',
            'Descripción Material', 'División', 'Marca',
            'Entrega', 'Cantidad', 'Placa Camión',
        ]
        for col_idx, col_name in enumerate(columns, 1):
            ws.cell(row=1, column=col_idx, value=col_name)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_pauta_complejidad.xlsx"'
        return response

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        Subir archivo Excel, parsear, validar y retornar vista previa
        sin guardar pautas.
        """
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No se proporcionó archivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dc = get_user_distributor_center(request)
        if not dc:
            return Response(
                {'error': 'Usuario sin centro de distribución asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            wb = openpyxl.load_workbook(file, read_only=True)
            ws = wb.active
        except Exception:
            return Response(
                {'error': 'No se pudo leer el archivo Excel.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = list(ws.iter_rows(min_row=2, values_only=True))
        errors = []
        pautas_grouped = defaultdict(lambda: {
            'transport_number': '',
            'trip_number': '',
            'route_code': '',
            'truck_plate': '',
            'products': [],
            'deliveries': [],
            'total_boxes': 0,
            'total_skus': set(),
        })

        for row_idx, row in enumerate(rows, start=2):
            if len(row) < 10:
                errors.append(f"Fila {row_idx}: columnas insuficientes.")
                continue

            transporte = str(row[0] or '').strip()
            viaje = str(row[1] or '').strip()
            ruta = str(row[2] or '').strip()
            material = str(row[3] or '').strip()
            descripcion = str(row[4] or '').strip()
            division = str(row[5] or '').strip()
            marca = str(row[6] or '').strip()
            entrega = str(row[7] or '').strip()
            cantidad = row[8]
            placa = str(row[9] or '').strip()

            if not transporte:
                errors.append(f"Fila {row_idx}: Transporte es requerido.")
                continue

            try:
                cantidad = int(cantidad) if cantidad else 0
            except (ValueError, TypeError):
                errors.append(f"Fila {row_idx}: Cantidad inválida '{cantidad}'.")
                continue

            key = f"{transporte}|{viaje}"
            group = pautas_grouped[key]
            group['transport_number'] = transporte
            group['trip_number'] = viaje
            group['route_code'] = ruta
            group['truck_plate'] = placa
            group['total_boxes'] += cantidad
            group['total_skus'].add(material)
            group['products'].append({
                'material_code': material,
                'product_name': descripcion,
                'division': division,
                'brand': marca,
                'total_boxes': cantidad,
            })
            group['deliveries'].append({
                'route_code': ruta,
                'delivery_number': entrega,
                'material_code': material,
                'delivery_quantity': cantidad,
            })

        # Crear el registro de upload en estado PREVIEW
        upload = PalletComplexUploadModel.objects.create(
            file_name=file.name,
            file=file,
            status='PREVIEW',
            errors_json={'errors': errors},
            row_count=len(rows),
            distributor_center=dc,
            uploaded_by=request.user,
        )

        # Preparar respuesta
        preview_pautas = []
        for key, group in pautas_grouped.items():
            preview_pautas.append({
                'transport_number': group['transport_number'],
                'trip_number': group['trip_number'],
                'route_code': group['route_code'],
                'truck_plate': group['truck_plate'],
                'total_boxes': group['total_boxes'],
                'total_skus': len(group['total_skus']),
                'products_count': len(group['products']),
                'deliveries_count': len(group['deliveries']),
            })

        return Response({
            'upload_id': upload.id,
            'file_name': file.name,
            'row_count': len(rows),
            'pautas_count': len(preview_pautas),
            'errors': errors,
            'pautas': preview_pautas,
        })

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirmar una carga y crear las pautas a partir del archivo subido.
        """
        upload = self.get_object()

        if upload.status != 'PREVIEW':
            return Response(
                {'error': 'Solo se pueden confirmar cargas en estado Vista Previa.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dc = get_user_distributor_center(request)
        if not dc:
            return Response(
                {'error': 'Usuario sin centro de distribución asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        operational_date = request.data.get('operational_date', timezone.now().date())

        try:
            wb = openpyxl.load_workbook(upload.file, read_only=True)
            ws = wb.active
        except Exception:
            return Response(
                {'error': 'No se pudo leer el archivo guardado.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        rows = list(ws.iter_rows(min_row=2, values_only=True))

        # Agrupar por Transporte+Viaje
        pautas_grouped = defaultdict(lambda: {
            'transport_number': '',
            'trip_number': '',
            'route_code': '',
            'truck_plate': '',
            'products': [],
            'deliveries': [],
            'total_boxes': 0,
            'total_skus': set(),
        })

        for row in rows:
            if len(row) < 10:
                continue
            transporte = str(row[0] or '').strip()
            viaje = str(row[1] or '').strip()
            ruta = str(row[2] or '').strip()
            material = str(row[3] or '').strip()
            descripcion = str(row[4] or '').strip()
            division = str(row[5] or '').strip()
            marca = str(row[6] or '').strip()
            entrega = str(row[7] or '').strip()
            try:
                cantidad = int(row[8]) if row[8] else 0
            except (ValueError, TypeError):
                continue
            placa = str(row[9] or '').strip()

            if not transporte:
                continue

            key = f"{transporte}|{viaje}"
            group = pautas_grouped[key]
            group['transport_number'] = transporte
            group['trip_number'] = viaje
            group['route_code'] = ruta
            group['truck_plate'] = placa
            group['total_boxes'] += cantidad
            group['total_skus'].add(material)
            group['products'].append({
                'material_code': material,
                'product_name': descripcion,
                'division': division,
                'brand': marca,
                'total_boxes': cantidad,
            })
            group['deliveries'].append({
                'route_code': ruta,
                'delivery_number': entrega,
                'material_code': material,
                'delivery_quantity': cantidad,
            })

        created_pautas = []
        for key, group in pautas_grouped.items():
            # Buscar camión por placa
            truck = TruckModel.objects.filter(
                plate=group['truck_plate'],
                distributor_center=dc,
                is_active=True,
            ).first()

            if not truck:
                # Crear camión si no existe
                truck = TruckModel.objects.create(
                    code=group['truck_plate'],
                    plate=group['truck_plate'],
                    pallet_type='STANDARD',
                    pallet_spaces=0,
                    distributor_center=dc,
                )

            total_skus = len(group['total_skus'])

            pauta = PautaModel.objects.create(
                transport_number=group['transport_number'],
                trip_number=group['trip_number'],
                route_code=group['route_code'],
                total_boxes=group['total_boxes'],
                total_skus=total_skus,
                status='PENDING_PICKING',
                operational_date=operational_date,
                truck=truck,
                upload=upload,
                distributor_center=dc,
            )

            # Crear detalles de producto (agrupados por material)
            product_totals = defaultdict(lambda: {
                'product_name': '',
                'total_boxes': 0,
            })
            for prod in group['products']:
                mat = prod['material_code']
                product_totals[mat]['product_name'] = prod['product_name']
                product_totals[mat]['total_boxes'] += prod['total_boxes']

            for mat_code, prod_data in product_totals.items():
                # Buscar en catálogo
                catalog_product = ProductCatalogModel.objects.filter(
                    sku_code=mat_code,
                    distributor_center=dc,
                ).first()

                boxes_per_pallet = catalog_product.boxes_per_pallet if catalog_product else 1
                full_pallets = prod_data['total_boxes'] // boxes_per_pallet if boxes_per_pallet > 0 else 0
                fraction_boxes = prod_data['total_boxes'] % boxes_per_pallet if boxes_per_pallet > 0 else 0
                fraction = Decimal(str(fraction_boxes)) / Decimal(str(boxes_per_pallet)) if boxes_per_pallet > 0 else Decimal('0')

                PautaProductDetailModel.objects.create(
                    material_code=mat_code,
                    product_name=prod_data['product_name'],
                    total_boxes=prod_data['total_boxes'],
                    full_pallets=full_pallets,
                    fraction=fraction,
                    pauta=pauta,
                    product_catalog=catalog_product,
                )

            # Crear detalles de entrega
            for deliv in group['deliveries']:
                PautaDeliveryDetailModel.objects.create(
                    route_code=deliv['route_code'],
                    delivery_number=deliv['delivery_number'],
                    material_code=deliv['material_code'],
                    delivery_quantity=deliv['delivery_quantity'],
                    pauta=pauta,
                )

            created_pautas.append(pauta.id)

        upload.status = 'CONFIRMED'
        upload.save(update_fields=['status'])

        return Response({
            'message': f'Se crearon {len(created_pautas)} pautas exitosamente.',
            'upload_id': upload.id,
            'pauta_ids': created_pautas,
        })


class PautaViewSet(viewsets.ModelViewSet):
    """Gestión de pautas del ciclo del camión"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PautaFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return PautaListSerializer
        return PautaDetailSerializer

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return PautaModel.objects.filter(
                distributor_center=dc
            ).select_related('truck', 'upload', 'distributor_center')
        return PautaModel.objects.none()

    def _do_transition(self, request, pk, action_name):
        """Ejecutar una transición de estado"""
        pauta = self.get_object()
        transition = STATUS_TRANSITIONS.get(action_name)

        if not transition:
            return Response(
                {'error': f'Acción "{action_name}" no reconocida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pauta.status not in transition['from']:
            return Response(
                {'error': f'No se puede ejecutar "{action_name}" desde el estado "{pauta.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pauta.status = transition['to']
        pauta.save(update_fields=['status'])

        # Crear timestamp si corresponde
        if transition['event']:
            PautaTimestampModel.objects.create(
                event_type=transition['event'],
                pauta=pauta,
                recorded_by=request.user,
                notes=request.data.get('notes', ''),
            )

        serializer = PautaDetailSerializer(pauta)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_picker(self, request, pk=None):
        """Asignar picker a la pauta"""
        response = self._do_transition(request, pk, 'assign_picker')
        if response.status_code == 200:
            pauta = self.get_object()
            personnel_id = request.data.get('personnel_id')
            if personnel_id:
                PautaAssignmentModel.objects.create(
                    role='PICKER',
                    pauta=pauta,
                    personnel_id=personnel_id,
                    assigned_by=request.user,
                )
        return response

    @action(detail=True, methods=['post'])
    def start_picking(self, request, pk=None):
        return self._do_transition(request, pk, 'start_picking')

    @action(detail=True, methods=['post'])
    def complete_picking(self, request, pk=None):
        return self._do_transition(request, pk, 'complete_picking')

    @action(detail=True, methods=['post'])
    def assign_bay(self, request, pk=None):
        """Asignar andén a la pauta"""
        response = self._do_transition(request, pk, 'assign_bay')
        if response.status_code == 200:
            from apps.truck_cycle.models.operational import PautaBayAssignmentModel
            pauta = self.get_object()
            bay_id = request.data.get('bay_id')
            if bay_id:
                PautaBayAssignmentModel.objects.update_or_create(
                    pauta=pauta,
                    defaults={
                        'bay_id': bay_id,
                        'assigned_by': request.user,
                    }
                )
        return response

    @action(detail=True, methods=['post'])
    def complete_loading(self, request, pk=None):
        return self._do_transition(request, pk, 'complete_loading')

    @action(detail=True, methods=['post'])
    def assign_counter(self, request, pk=None):
        """Asignar contador a la pauta"""
        response = self._do_transition(request, pk, 'assign_counter')
        if response.status_code == 200:
            pauta = self.get_object()
            personnel_id = request.data.get('personnel_id')
            if personnel_id:
                PautaAssignmentModel.objects.create(
                    role='COUNTER',
                    pauta=pauta,
                    personnel_id=personnel_id,
                    assigned_by=request.user,
                )
        return response

    @action(detail=True, methods=['post'])
    def complete_count(self, request, pk=None):
        return self._do_transition(request, pk, 'complete_count')

    @action(detail=True, methods=['post'])
    def checkout_security(self, request, pk=None):
        return self._do_transition(request, pk, 'checkout_security')

    @action(detail=True, methods=['post'])
    def checkout_ops(self, request, pk=None):
        return self._do_transition(request, pk, 'checkout_ops')

    @action(detail=True, methods=['post'])
    def dispatch(self, request, pk=None):
        return self._do_transition(request, pk, 'dispatch')

    @action(detail=True, methods=['post'])
    def arrival(self, request, pk=None):
        return self._do_transition(request, pk, 'arrival')

    @action(detail=True, methods=['post'])
    def process_return(self, request, pk=None):
        return self._do_transition(request, pk, 'process_return')

    @action(detail=True, methods=['post'])
    def start_audit(self, request, pk=None):
        return self._do_transition(request, pk, 'start_audit')

    @action(detail=True, methods=['post'])
    def complete_audit(self, request, pk=None):
        return self._do_transition(request, pk, 'complete_audit')

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        return self._do_transition(request, pk, 'close')

    @action(detail=False, methods=['get'])
    def workstation(self, request):
        """Agrupar pautas por estado para vista de estación de trabajo"""
        qs = self.get_queryset()
        operational_date = request.query_params.get('operational_date')
        if operational_date:
            qs = qs.filter(operational_date=operational_date)

        grouped = {}
        for choice_value, choice_label in PautaModel.STATUS_CHOICES:
            pautas = qs.filter(status=choice_value)
            grouped[choice_value] = {
                'label': choice_label,
                'count': pautas.count(),
                'pautas': PautaListSerializer(pautas, many=True).data,
            }

        return Response(grouped)

    @action(detail=False, methods=['get'])
    def reload_queue(self, request):
        """Pautas en cola de recarga ordenadas por fecha de creación"""
        qs = self.get_queryset().filter(
            status='IN_RELOAD_QUEUE'
        ).order_by('created_at')
        serializer = PautaListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def kpi_summary(self, request):
        """Resumen de KPIs agregados"""
        qs = self.get_queryset()
        operational_date = request.query_params.get('operational_date')
        if operational_date:
            qs = qs.filter(operational_date=operational_date)

        total_pautas = qs.count()
        dispatched = qs.filter(status='DISPATCHED').count()
        closed = qs.filter(status='CLOSED').count()
        total_boxes = qs.aggregate(total=Sum('total_boxes'))['total'] or 0
        avg_complexity = qs.aggregate(avg=Avg('complexity_score'))['avg'] or 0

        # Conteo de inconsistencias
        from apps.truck_cycle.models.operational import InconsistencyModel
        inconsistency_count = InconsistencyModel.objects.filter(
            pauta__in=qs
        ).count()

        return Response({
            'total_pautas': total_pautas,
            'dispatched': dispatched,
            'closed': closed,
            'total_boxes': total_boxes,
            'avg_complexity': round(float(avg_complexity), 2),
            'inconsistency_count': inconsistency_count,
        })
