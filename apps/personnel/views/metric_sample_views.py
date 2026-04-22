"""Endpoints para samples de métricas operativas y agregados en vivo."""
from decimal import Decimal

from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.personnel.models.metric_sample import PersonnelMetricSample
from apps.personnel.serializers.metric_sample_serializers import (
    PersonnelMetricSampleSerializer,
)


class PersonnelMetricSampleViewSet(viewsets.ReadOnlyModelViewSet):
    """Samples históricos (una fila por evento medido).

    Filtros: ?personnel=, ?metric_type=, ?operational_date=,
    ?operational_date_after=, ?operational_date_before=, ?source=.
    """
    serializer_class = PersonnelMetricSampleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'personnel': ['exact'],
        'metric_type': ['exact'],
        'operational_date': ['exact', 'gte', 'lte'],
        'source': ['exact'],
    }

    def get_queryset(self):
        return (
            PersonnelMetricSample.objects
            .select_related('personnel', 'metric_type')
            .all()
        )

    @action(detail=False, methods=['get'], url_path='live')
    def live(self, request):
        """Agregados del día (on-demand) por personnel o por rol.

        Query params:
            operational_date: YYYY-MM-DD (default: hoy)
            personnel_id:     filtra a una sola persona
            distributor_center: filtra por CD (para agregados por rol)

        Respuesta:
            {
              date, personnel_id,
              picker: { pallets_per_hour, loads_assembled,
                        avg_time_per_pauta_min, load_error_rate_pct, samples_count },
              counter: { pallets_per_hour, avg_time_per_truck_min,
                         error_rate_pct, samples_count },
              yard:    { trucks_moved, avg_park_to_bay_min,
                         avg_bay_to_park_min, avg_total_move_min, samples_count },
            }
        """
        op_date_str = request.query_params.get('operational_date')
        try:
            op_date = (
                timezone.datetime.fromisoformat(op_date_str).date()
                if op_date_str else timezone.localdate()
            )
        except (TypeError, ValueError):
            op_date = timezone.localdate()

        personnel_id = request.query_params.get('personnel_id')
        dc_id = request.query_params.get('distributor_center')

        samples_qs = PersonnelMetricSample.objects.filter(operational_date=op_date)
        if personnel_id:
            samples_qs = samples_qs.filter(personnel_id=personnel_id)

        def _avg(code):
            row = samples_qs.filter(metric_type__code=code).aggregate(avg=Avg('numeric_value'))
            return float(row['avg']) if row['avg'] is not None else None

        def _count(code):
            return samples_qs.filter(metric_type__code=code).count()

        # ---------- Datos de truck_cycle para los agregados no-sample ----------
        from apps.truck_cycle.models.core import PautaModel
        from apps.truck_cycle.models.operational import (
            PautaAssignmentModel,
            InconsistencyModel,
        )

        pauta_qs = PautaModel.objects.filter(operational_date=op_date)
        if dc_id:
            pauta_qs = pauta_qs.filter(distributor_center_id=dc_id)

        # ----- Picker -----
        picker_pauta_filter = Q(assignments__role='PICKER')
        if personnel_id:
            picker_pauta_filter &= Q(assignments__personnel_id=personnel_id)
        picker_pautas = pauta_qs.filter(picker_pauta_filter).distinct()

        fractions_sum = picker_pautas.aggregate(total=Sum('assembled_fractions'))['total'] or 0
        loads_assembled = picker_pautas.filter(status__in=[
            'PICKING_DONE', 'MOVING_TO_BAY', 'IN_BAY', 'PENDING_COUNT', 'COUNTING',
            'COUNTED', 'CHECKOUT_SECURITY', 'CHECKOUT_OPS', 'DISPATCHED', 'CLOSED',
        ]).count()

        avg_time_per_pauta = _avg('picker_time_per_pauta')  # min
        picker_total_minutes = (
            samples_qs.filter(metric_type__code='picker_time_per_pauta')
            .aggregate(t=Sum('numeric_value'))['t']
        )
        picker_hours = float(picker_total_minutes) / 60.0 if picker_total_minutes else 0.0
        pallets_per_hour_picker = (fractions_sum / picker_hours) if picker_hours > 0 else None

        # Errores de carga: inconsistencies fase VERIFICATION
        ver_errors = InconsistencyModel.objects.filter(
            pauta__in=picker_pautas,
            phase='VERIFICATION',
        ).aggregate(total=Sum('difference'))['total'] or 0
        total_boxes_picker = picker_pautas.aggregate(t=Sum('total_boxes'))['t'] or 0
        load_error_rate = (
            (abs(ver_errors) / total_boxes_picker) * 100
            if total_boxes_picker > 0 else None
        )

        # ----- Counter -----
        counter_pauta_filter = Q(assignments__role='COUNTER')
        if personnel_id:
            counter_pauta_filter &= Q(assignments__personnel_id=personnel_id)
        counter_pautas = pauta_qs.filter(counter_pauta_filter).distinct()

        avg_time_per_truck = _avg('counter_time_per_truck')
        counter_total_minutes = (
            samples_qs.filter(metric_type__code='counter_time_per_truck')
            .aggregate(t=Sum('numeric_value'))['t']
        )
        counter_hours = float(counter_total_minutes) / 60.0 if counter_total_minutes else 0.0
        total_pallets_counted = float(
            counter_pautas.aggregate(t=Sum('total_pallets'))['t'] or 0
        )
        pallets_per_hour_counter = (
            total_pallets_counted / counter_hours if counter_hours > 0 else None
        )

        # Errores de conteo: inconsistencies fase CHECKOUT.
        co_errors = InconsistencyModel.objects.filter(
            pauta__in=counter_pautas,
            phase='CHECKOUT',
        ).aggregate(total=Sum('difference'))['total'] or 0
        total_boxes_counter = counter_pautas.aggregate(t=Sum('total_boxes'))['t'] or 0
        counter_error_rate = (
            (abs(co_errors) / total_boxes_counter) * 100
            if total_boxes_counter > 0 else None
        )

        # ----- Yard driver -----
        trucks_moved_count = PautaAssignmentModel.objects.filter(
            role='YARD_DRIVER',
            pauta__operational_date=op_date,
            **({'personnel_id': personnel_id} if personnel_id else {}),
            **({'pauta__distributor_center_id': dc_id} if dc_id else {}),
        ).values('pauta_id').distinct().count()

        return Response({
            'date': str(op_date),
            'personnel_id': int(personnel_id) if personnel_id else None,
            'picker': {
                'pallets_per_hour':        _round(pallets_per_hour_picker),
                'loads_assembled':         loads_assembled,
                'fractions_assembled':     fractions_sum,
                'avg_time_per_pauta_min':  _round(avg_time_per_pauta),
                'load_error_rate_pct':     _round(load_error_rate),
                'samples_count':           _count('picker_time_per_pauta'),
            },
            'counter': {
                'pallets_per_hour':        _round(pallets_per_hour_counter),
                'avg_time_per_truck_min':  _round(avg_time_per_truck),
                'error_rate_pct':          _round(counter_error_rate),
                'samples_count':           _count('counter_time_per_truck'),
            },
            'yard': {
                'trucks_moved':            trucks_moved_count,
                'avg_park_to_bay_min':     _round(_avg('yard_time_park_to_bay')),
                'avg_bay_to_park_min':     _round(_avg('yard_time_bay_to_park')),
                'avg_total_move_min':      _round(_avg('yard_time_total_move')),
                'samples_count':           _count('yard_time_park_to_bay') + _count('yard_time_bay_to_park'),
            },
        })


def _round(value, digits=2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None
