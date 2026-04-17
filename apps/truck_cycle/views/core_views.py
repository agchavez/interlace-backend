"""
ViewSets para modelos principales del ciclo del camión
"""
import io
from collections import defaultdict
from datetime import date
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
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from apps.truck_cycle.models.catalogs import TruckModel, ProductCatalogModel
from apps.truck_cycle.models.core import (
    PalletComplexUploadModel,
    PautaModel,
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
    """Obtener el centro de distribución seleccionado por el usuario"""
    try:
        if request.user.centro_distribucion_id:
            return request.user.centro_distribucion
        return request.user.personnel_profile.primary_distributor_center
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
        """Descargar plantilla Excel con las columnas esperadas (nivel resumen por transporte)"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pautas"

        columns = [
            ('Viaje', 12),
            ('Transporte', 18),
            ('Camión', 15),
            ('Placa', 15),
            ('Ruta', 15),
            ('Cajas', 12),
            ('SKUs', 12),
            ('Pallets Completos', 18),
            ('Complejidad', 15),
        ]

        header_font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
        header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        for col_idx, (col_name, width) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        # Ejemplo de fila
        example = [1, '4000825134', 'HN-1264', 'PBR-4521', 'R-TGU-01', 775, 55, 1, 7.52]
        for col_idx, val in enumerate(example, 1):
            ws.cell(row=2, column=col_idx, value=val)

        ws.freeze_panes = 'A2'

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_pautas.xlsx"'
        return response

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        Subir archivo Excel con pautas a nivel resumen (1 fila = 1 pauta).
        Columnas: Viaje, Transporte, Camión, Placa, Ruta, Cajas, SKUs, Pallets Completos, Complejidad
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
        warnings = []
        pautas = []

        for row_idx, row in enumerate(rows, start=2):
            if not row or all(c is None for c in row):
                continue

            if len(row) < 6:
                errors.append(f"Fila {row_idx}: columnas insuficientes (mínimo 6).")
                continue

            viaje = str(row[0] or '').strip()
            transporte = str(row[1] or '').strip()
            camion = str(row[2] or '').strip()
            placa = str(row[3] or '').strip()
            ruta = str(row[4] or '').strip()

            if not transporte:
                errors.append(f"Fila {row_idx}: Transporte es requerido.")
                continue
            if not viaje:
                errors.append(f"Fila {row_idx}: Viaje es requerido.")
                continue

            try:
                cajas = int(float(row[5])) if row[5] else 0
            except (ValueError, TypeError):
                errors.append(f"Fila {row_idx}: Cajas inválido '{row[5]}'.")
                continue

            try:
                skus = int(float(row[6])) if len(row) > 6 and row[6] else 0
            except (ValueError, TypeError):
                skus = 0

            try:
                completas = int(float(row[7])) if len(row) > 7 and row[7] else 0
            except (ValueError, TypeError):
                completas = 0

            try:
                complejidad = round(float(row[8]), 2) if len(row) > 8 and row[8] else 0
            except (ValueError, TypeError):
                complejidad = 0

            if not camion and not placa:
                warnings.append(f"Fila {row_idx}: Sin camión ni placa asignada.")

            pautas.append({
                'trip_number': viaje,
                'transport_number': transporte,
                'truck_code': camion,
                'truck_plate': placa,
                'route_code': ruta,
                'total_boxes': cajas,
                'total_skus': skus,
                'full_pallets': completas,
                'complexity_score': complejidad,
            })

        # Crear registro de upload en estado PREVIEW
        upload = PalletComplexUploadModel.objects.create(
            file_name=file.name,
            file=file,
            status='PREVIEW',
            errors_json={'errors': errors},
            row_count=len(rows),
            distributor_center=dc,
            uploaded_by=request.user,
        )

        return Response({
            'upload_id': upload.id,
            'file_name': file.name,
            'row_count': len(rows),
            'pautas_count': len(pautas),
            'errors': errors,
            'warnings': warnings,
            'pautas_preview': pautas,
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
        created_pautas = []

        for row in rows:
            if not row or all(c is None for c in row):
                continue
            if len(row) < 6:
                continue

            viaje = str(row[0] or '').strip()
            transporte = str(row[1] or '').strip()
            camion_code = str(row[2] or '').strip()
            placa = str(row[3] or '').strip()
            ruta = str(row[4] or '').strip()

            if not transporte or not viaje:
                continue

            try:
                cajas = int(float(row[5])) if row[5] else 0
            except (ValueError, TypeError):
                continue

            try:
                skus = int(float(row[6])) if len(row) > 6 and row[6] else 0
            except (ValueError, TypeError):
                skus = 0

            try:
                completas = int(float(row[7])) if len(row) > 7 and row[7] else 0
            except (ValueError, TypeError):
                completas = 0

            try:
                complejidad = round(float(row[8]), 2) if len(row) > 8 and row[8] else 0
            except (ValueError, TypeError):
                complejidad = 0

            # Buscar camión por código o placa
            truck = None
            if camion_code:
                truck = TruckModel.objects.filter(
                    code=camion_code, distributor_center=dc, is_active=True,
                ).first()
            if not truck and placa:
                truck = TruckModel.objects.filter(
                    plate=placa, distributor_center=dc, is_active=True,
                ).first()
            if not truck:
                # Crear camión con los datos disponibles
                truck = TruckModel.objects.create(
                    code=camion_code or placa,
                    plate=placa or camion_code,
                    pallet_type='STANDARD',
                    pallet_spaces=0,
                    distributor_center=dc,
                )

            pauta = PautaModel.objects.create(
                transport_number=transporte,
                trip_number=viaje,
                route_code=ruta,
                total_boxes=cajas,
                total_skus=skus,
                total_pallets=completas,
                complexity_score=complejidad,
                status='PENDING_PICKING',
                operational_date=operational_date,
                truck=truck,
                upload=upload,
                distributor_center=dc,
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
        """Asignar andén y chofer de patio a la pauta"""
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
            # Asignar chofer de patio si se proporcionó
            yard_driver_id = request.data.get('yard_driver_id')
            if yard_driver_id:
                PautaAssignmentModel.objects.create(
                    role='YARD_DRIVER',
                    pauta=pauta,
                    personnel_id=yard_driver_id,
                    assigned_by=request.user,
                )
        return response

    @action(detail=True, methods=['post'])
    def complete_loading(self, request, pk=None):
        response = self._do_transition(request, pk, 'complete_loading')
        if response.status_code == 200:
            pauta = self.get_object()
            bay_assignment = getattr(pauta, 'bay_assignment', None)
            if bay_assignment and not bay_assignment.released_at:
                bay_assignment.released_at = timezone.now()
                bay_assignment.save(update_fields=['released_at'])
        return response

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
        """Validación de seguridad en checkout"""
        response = self._do_transition(request, pk, 'checkout_security')
        if response.status_code == 200:
            from apps.truck_cycle.models.operational import CheckoutValidationModel
            pauta = self.get_object()
            checkout, _ = CheckoutValidationModel.objects.get_or_create(pauta=pauta)
            checkout.security_validated = True
            checkout.security_validated_at = timezone.now()
            validator_id = request.data.get('validator_id')
            if validator_id:
                checkout.security_validator_id = validator_id
            exit_pass = request.data.get('exit_pass_consumables')
            if exit_pass is not None:
                checkout.exit_pass_consumables = exit_pass
            checkout.save()
        return response

    @action(detail=True, methods=['post'])
    def checkout_ops(self, request, pk=None):
        """Validación de operaciones en checkout"""
        response = self._do_transition(request, pk, 'checkout_ops')
        if response.status_code == 200:
            from apps.truck_cycle.models.operational import CheckoutValidationModel
            pauta = self.get_object()
            checkout, _ = CheckoutValidationModel.objects.get_or_create(pauta=pauta)
            checkout.ops_validated = True
            checkout.ops_validated_at = timezone.now()
            validator_id = request.data.get('validator_id')
            if validator_id:
                checkout.ops_validator_id = validator_id
            checkout.save()
        return response

    @action(detail=True, methods=['post'], url_path='dispatch', url_name='dispatch')
    def dispatch_truck(self, request, pk=None):
        return self._do_transition(request, pk, 'dispatch')

    @action(detail=True, methods=['post'])
    def arrival(self, request, pk=None):
        return self._do_transition(request, pk, 'arrival')

    @action(detail=False, methods=['post'], url_path='public-arrival/(?P<truck_code>[^/.]+)',
            permission_classes=[permissions.AllowAny], authentication_classes=[])
    def public_arrival(self, request, truck_code=None):
        """Registro público de llegada — el chofer escanea QR en el bunker"""
        from apps.truck_cycle.models.catalogs import TruckModel
        truck = TruckModel.objects.filter(code=truck_code, is_active=True).first()
        if not truck:
            truck = TruckModel.objects.filter(plate=truck_code, is_active=True).first()
        if not truck:
            return Response({'error': 'Camión no encontrado'}, status=404)

        pauta = PautaModel.objects.filter(
            truck=truck, status='DISPATCHED'
        ).order_by('-created_at').first()
        if not pauta:
            return Response({'error': 'No hay pautas despachadas para este camión'}, status=404)

        transition = STATUS_TRANSITIONS['arrival']
        pauta.status = transition['to']
        pauta.save(update_fields=['status'])
        if transition['event']:
            from apps.truck_cycle.models.operational import PautaTimestampModel
            PautaTimestampModel.objects.create(
                pauta=pauta, event_type=transition['event']
            )
        return Response({
            'message': f'Llegada registrada para T-{pauta.transport_number}',
            'transport_number': pauta.transport_number,
            'truck_code': truck.code,
            'truck_plate': truck.plate,
        })

    @action(detail=False, methods=['get'], url_path='public-truck-status/(?P<truck_code>[^/.]+)',
            permission_classes=[permissions.AllowAny], authentication_classes=[])
    def public_truck_status(self, request, truck_code=None):
        """Status público del camión para la página de QR"""
        from apps.truck_cycle.models.catalogs import TruckModel
        truck = TruckModel.objects.filter(code=truck_code, is_active=True).first()
        if not truck:
            truck = TruckModel.objects.filter(plate=truck_code, is_active=True).first()
        if not truck:
            return Response({'error': 'Camión no encontrado'}, status=404)

        pauta = PautaModel.objects.filter(
            truck=truck
        ).exclude(status__in=['CLOSED', 'CANCELLED']).order_by('-created_at').first()

        return Response({
            'truck_code': truck.code,
            'truck_plate': truck.plate,
            'has_active_pauta': pauta is not None,
            'status': pauta.status if pauta else None,
            'status_display': pauta.get_status_display() if pauta else None,
            'transport_number': pauta.transport_number if pauta else None,
            'can_register_arrival': pauta.status == 'DISPATCHED' if pauta else False,
        })

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
        """Resumen de KPIs agregados con productividad y TAR"""
        qs = self.get_queryset()
        operational_date = request.query_params.get('operational_date')
        if operational_date:
            qs = qs.filter(operational_date=operational_date)

        total_pautas = qs.count()
        dispatched = qs.filter(status='DISPATCHED').count()
        closed = qs.filter(status='CLOSED').count()
        completed_pautas = dispatched + closed
        total_boxes = qs.aggregate(total=Sum('total_boxes'))['total'] or 0

        from apps.truck_cycle.models.operational import InconsistencyModel
        inconsistency_count = InconsistencyModel.objects.filter(
            pauta__in=qs
        ).count()

        # Calcular productividad de picking (cajas/hora)
        avg_boxes_per_hour = None
        picking_pautas = qs.exclude(status='PENDING_PICKING')
        picking_rates = []
        for pauta in picking_pautas:
            t0 = pauta.timestamps.filter(event_type='T0_PICKING_START').first()
            t1 = pauta.timestamps.filter(event_type='T1_PICKING_END').first()
            if t0 and t1:
                delta_hours = (t1.timestamp - t0.timestamp).total_seconds() / 3600
                if delta_hours >= 0.05:  # al menos 3 minutos
                    picking_rates.append(pauta.total_boxes / delta_hours)
        if picking_rates:
            avg_boxes_per_hour = round(sum(picking_rates) / len(picking_rates), 1)

        # Calcular TAR promedio (minutos)
        avg_tar_minutes = None
        tar_values = []
        for pauta in qs.filter(is_reload=True):
            t_arrival = pauta.timestamps.filter(event_type='T10_ARRIVAL').first()
            t_counted = pauta.timestamps.filter(event_type='T6_COUNT_END').first()
            if t_arrival and t_counted:
                tar_min = (t_counted.timestamp - t_arrival.timestamp).total_seconds() / 60
                if tar_min > 0:
                    tar_values.append(tar_min)
        if tar_values:
            avg_tar_minutes = round(sum(tar_values) / len(tar_values), 1)

        # Precisión de conteo
        avg_count_accuracy = None
        if total_pautas > 0:
            pautas_with_issues = InconsistencyModel.objects.filter(
                pauta__in=qs, phase='VERIFICATION'
            ).values('pauta').distinct().count()
            avg_count_accuracy = round(1 - (pautas_with_issues / total_pautas), 3) if total_pautas > 0 else None

        # Error rate de picking
        avg_picking_error_rate = None
        if total_pautas > 0:
            picking_errors = InconsistencyModel.objects.filter(
                pauta__in=qs, phase='VERIFICATION'
            ).count()
            avg_picking_error_rate = round(picking_errors / total_pautas, 3)

        # Status breakdown
        pautas_by_status = list(
            qs.values('status').annotate(count=Count('id')).order_by('status')
        )

        return Response({
            'operational_date': operational_date or str(timezone.now().date()),
            'total_pautas': total_pautas,
            'completed_pautas': completed_pautas,
            'dispatched': dispatched,
            'closed': closed,
            'total_boxes': total_boxes,
            'avg_boxes_per_hour': avg_boxes_per_hour,
            'avg_count_accuracy': avg_count_accuracy,
            'avg_picking_error_rate': avg_picking_error_rate,
            'avg_tar_minutes': avg_tar_minutes,
            'inconsistency_count': inconsistency_count,
            'pautas_by_status': pautas_by_status,
        })

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Descargar PDF de una pauta individual (estilo moderno con pdfkit)"""
        pauta = self.get_object()
        try:
            from apps.truck_cycle.utils.pdf_generator import generate_pauta_pdf
            pdf_buffer = generate_pauta_pdf(pauta)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="pauta_{pauta.transport_number}_V{pauta.trip_number}.pdf"'
            return response
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando PDF para pauta {pauta.id}: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return Response(
                {'error': 'Error al generar el documento PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='export_excel')
    def export_excel(self, request):
        """Exportar pautas a Excel"""
        qs = self.filter_queryset(self.get_queryset()).select_related('truck')
        today = date.today().strftime('%Y-%m-%d')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pautas"

        # Header style
        header_font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
        header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        thin_border = Border(
            left=Side(style='thin', color='E0E0E0'),
            right=Side(style='thin', color='E0E0E0'),
            top=Side(style='thin', color='E0E0E0'),
            bottom=Side(style='thin', color='E0E0E0'),
        )

        columns = [
            ('Transporte', 15), ('Viaje', 10), ('Ruta', 12), ('Camión', 20),
            ('Cajas', 10), ('SKUs', 10), ('Pallets', 10), ('Estado', 25),
            ('Fecha Operativa', 15), ('Recarga', 10),
        ]

        for col_idx, (col_name, width) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        ws.freeze_panes = 'A2'

        alt_fill = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
        cell_alignment = Alignment(vertical='center')

        for row_idx, pauta in enumerate(qs, start=2):
            values = [
                pauta.transport_number,
                pauta.trip_number,
                pauta.route_code,
                f"{pauta.truck.code} - {pauta.truck.plate}" if pauta.truck else '-',
                pauta.total_boxes,
                pauta.total_skus,
                pauta.total_pallets,
                pauta.get_status_display(),
                str(pauta.operational_date) if pauta.operational_date else '-',
                'Sí' if pauta.is_reload else 'No',
            ]
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.alignment = cell_alignment
                cell.border = thin_border
                if row_idx % 2 == 0:
                    cell.fill = alt_fill

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="pautas-{today}.xlsx"'
        return response

    @action(detail=False, methods=['get'], url_path='export_pdf')
    def export_pdf(self, request):
        """Exportar listado de pautas a PDF"""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import cm
        except ImportError:
            return Response(
                {'error': 'reportlab no está instalado.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        qs = self.filter_queryset(self.get_queryset()).select_related('truck')
        today = date.today().strftime('%Y-%m-%d')

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1976d2'))
        story.append(Paragraph("Listado de Pautas", title_style))
        meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
        story.append(Paragraph(f"Generado: {today} | Total: {qs.count()} registros", meta_style))
        story.append(Spacer(1, 12))

        data = [['Transporte', 'Viaje', 'Ruta', 'Camión', 'Cajas', 'SKUs', 'Estado', 'Fecha']]
        cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8)

        for pauta in qs[:500]:
            truck_str = f"{pauta.truck.code}-{pauta.truck.plate}" if pauta.truck else '-'
            data.append([
                pauta.transport_number,
                pauta.trip_number,
                pauta.route_code or '-',
                Paragraph(truck_str, cell_style),
                str(pauta.total_boxes),
                str(pauta.total_skus),
                pauta.get_status_display(),
                str(pauta.operational_date) if pauta.operational_date else '-',
            ])

        col_widths = [3*cm, 2*cm, 2.5*cm, 4*cm, 2*cm, 2*cm, 5*cm, 3*cm]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)

        doc.build(story)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="pautas-{today}.pdf"'
        return response
