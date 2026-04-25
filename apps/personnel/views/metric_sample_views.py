"""Endpoints para samples de métricas operativas y agregados en vivo."""
from decimal import Decimal

from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.personnel.models.metric_sample import PersonnelMetricSample
from apps.personnel.models.performance_new import PerformanceMetricType
from apps.personnel.serializers.metric_sample_serializers import (
    PersonnelMetricSampleSerializer,
)
from apps.personnel.utils.bands import band_for


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

        # Resolver DC para el join con KPITargetModel. Si viene personnel_id,
        # se usa su primary_distributor_center; si no, el dc_id del query.
        band_dc_id = dc_id
        if personnel_id and not band_dc_id:
            from apps.personnel.models.personnel import PersonnelProfile
            p = PersonnelProfile.objects.filter(pk=personnel_id).values_list(
                'primary_distributor_center_id', flat=True,
            ).first()
            band_dc_id = p

        # Cache de metric_type_id por code (una query)
        mt_map = dict(
            PerformanceMetricType.objects.filter(is_active=True)
            .values_list('code', 'id')
        )

        def _metric(code, value):
            """Wrap: devuelve dict con bandas listo para el frontend."""
            mt_id = mt_map.get(code)
            if not mt_id:
                return {'value': _round(value), 'target': None, 'trigger': None,
                        'direction': None, 'unit': None, 'band': 'GRAY'}
            result = band_for(value, mt_id, band_dc_id, op_date)
            result['value'] = _round(result['value'])
            result['target'] = _round(result['target'])
            result['trigger'] = _round(result['trigger'])
            return result

        return Response({
            'date': str(op_date),
            'personnel_id': int(personnel_id) if personnel_id else None,
            'distributor_center': band_dc_id,
            'picker': {
                'pallets_per_hour':        _metric('picker_pallets_per_hour', pallets_per_hour_picker),
                'loads_assembled':         _metric('picker_loads_assembled', loads_assembled),
                'fractions_assembled':     fractions_sum,
                'avg_time_per_pauta_min':  _metric('picker_time_per_pauta', avg_time_per_pauta),
                'load_error_rate_pct':     _metric('picker_load_error_rate', load_error_rate),
                'samples_count':           _count('picker_time_per_pauta'),
            },
            'counter': {
                'pallets_per_hour':        _metric('counter_pallets_per_hour', pallets_per_hour_counter),
                'avg_time_per_truck_min':  _metric('counter_time_per_truck', avg_time_per_truck),
                'error_rate_pct':          _metric('counter_error_rate', counter_error_rate),
                'samples_count':           _count('counter_time_per_truck'),
            },
            'yard': {
                'trucks_moved':            _metric('yard_trucks_moved', trucks_moved_count),
                'avg_park_to_bay_min':     _metric('yard_time_park_to_bay', _avg('yard_time_park_to_bay')),
                'avg_bay_to_park_min':     _metric('yard_time_bay_to_park', _avg('yard_time_bay_to_park')),
                'avg_total_move_min':      _metric('yard_time_total_move',  _avg('yard_time_total_move')),
                'samples_count':           _count('yard_time_park_to_bay') + _count('yard_time_bay_to_park'),
            },
        })

    @action(detail=False, methods=['get'], url_path='hourly')
    def hourly(self, request):
        """Serie por hora del día de una métrica dada.

        Query params:
            metric_code: código del PerformanceMetricType (requerido)
            operational_date: YYYY-MM-DD (default: hoy)
            distributor_center: opcional (restringe a personnel del CD)
            personnel_id: opcional (restringe a una persona)

        Respuesta:
            {
              date, metric_code, target, trigger, direction, unit,
              hours: [{hour: 0, value: null|float, band: 'GREEN|YELLOW|RED|GRAY', count: n}]
            }
        """
        from django.db.models import Avg, Count
        from django.db.models.functions import Extract

        metric_code = request.query_params.get('metric_code')
        if not metric_code:
            return Response({'error': 'metric_code requerido'}, status=400)

        op_date_str = request.query_params.get('operational_date')
        try:
            op_date = (
                timezone.datetime.fromisoformat(op_date_str).date()
                if op_date_str else timezone.localdate()
            )
        except (TypeError, ValueError):
            op_date = timezone.localdate()

        dc_id = request.query_params.get('distributor_center')
        personnel_id = request.query_params.get('personnel_id')

        try:
            mt = PerformanceMetricType.objects.get(code=metric_code)
        except PerformanceMetricType.DoesNotExist:
            return Response({'error': f'metric {metric_code} no existe'}, status=404)

        qs = PersonnelMetricSample.objects.filter(
            operational_date=op_date, metric_type=mt,
        )
        if dc_id:
            qs = qs.filter(personnel__primary_distributor_center_id=dc_id)
        if personnel_id:
            qs = qs.filter(personnel_id=personnel_id)

        agg = (
            qs.annotate(h=Extract('created_at', 'hour'))
            .values('h')
            .annotate(avg=Avg('numeric_value'), n=Count('id'))
            .order_by('h')
        )
        by_hour = {row['h']: row for row in agg}

        # Target/dirección vigentes.
        from apps.truck_cycle.models.catalogs import KPITargetModel
        target_obj = (
            KPITargetModel.objects
            .filter(metric_type=mt, effective_from__lte=op_date)
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=op_date))
        )
        if dc_id:
            target_obj = target_obj.filter(distributor_center_id=dc_id)
        target_obj = target_obj.order_by('-effective_from').first()

        from apps.personnel.utils.bands import compute_band
        target = float(target_obj.target_value) if target_obj else None
        trigger = float(target_obj.warning_threshold) if target_obj and target_obj.warning_threshold is not None else None
        direction = target_obj.direction if target_obj else None

        hours = []
        for h in range(24):
            row = by_hour.get(h)
            if row:
                v = float(row['avg'])
                band = compute_band(v, target, trigger, direction) if target_obj else 'GRAY'
                hours.append({'hour': h, 'value': round(v, 2), 'band': band, 'count': row['n']})
            else:
                hours.append({'hour': h, 'value': None, 'band': 'GRAY', 'count': 0})

        # Turno vigente del CD: coincide con día de semana + hora local HN.
        shift_info = None
        if dc_id:
            from apps.maintenance.models.distributor_center import DCShiftModel
            from zoneinfo import ZoneInfo
            now_hn = timezone.localtime(timezone.now(), ZoneInfo('America/Tegucigalpa'))
            day_map = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
            dow = day_map[now_hn.weekday()]
            today_shifts = list(
                DCShiftModel.objects.filter(
                    distributor_center_id=dc_id,
                    day_of_week=dow,
                    is_active=True,
                ).order_by('start_time')
            )
            now_t = now_hn.time()

            def _is_in_shift(s, t):
                # Soporta turnos que cruzan medianoche (end < start).
                if s.start_time <= s.end_time:
                    return s.start_time <= t <= s.end_time
                return t >= s.start_time or t <= s.end_time

            active = next((s for s in today_shifts if _is_in_shift(s, now_t)), None)

            # Si no hay turno activo hoy, revisar los de ayer (caso: turno noche
            # empezó ayer y aún no termina).
            if not active:
                yesterday_dow = day_map[(now_hn.weekday() - 1) % 7]
                yesterday_shifts = DCShiftModel.objects.filter(
                    distributor_center_id=dc_id,
                    day_of_week=yesterday_dow,
                    is_active=True,
                )
                for s in yesterday_shifts:
                    if s.start_time > s.end_time and now_t <= s.end_time:
                        active = s
                        break

            target_shift = active or (today_shifts[0] if today_shifts else None)
            if target_shift:
                # Si cruza medianoche, end_hour efectivo es end_hour + 24 para
                # rango de horas visibles.
                end_h = target_shift.end_time.hour
                if target_shift.end_time <= target_shift.start_time:
                    end_h = target_shift.end_time.hour + 24
                shift_info = {
                    'name': target_shift.shift_name,
                    'day_of_week': target_shift.day_of_week,
                    'start_time': target_shift.start_time.strftime('%H:%M'),
                    'end_time': target_shift.end_time.strftime('%H:%M'),
                    'start_hour': target_shift.start_time.hour,
                    'end_hour': end_h,
                    'is_active_now': active is not None,
                    'current_hour': now_hn.hour,
                }

        return Response({
            'date': str(op_date),
            'metric_code': metric_code,
            'metric_name': mt.name,
            'unit': target_obj.unit if target_obj and target_obj.unit else mt.unit or '',
            'target': _round(target),
            'trigger': _round(trigger),
            'direction': direction,
            'hours': hours,
            'shift': shift_info,
        })

    @action(detail=False, methods=['get'], url_path='workstation')
    def workstation(self, request):
        """Vista de workstation por rol: lista de personnel + sus métricas del día.

        Query params:
            role: 'picker' | 'counter' | 'yard'   (obligatorio)
            operational_date: YYYY-MM-DD (default: hoy)
            distributor_center: ID (si no viene, se usa el del request)

        Respuesta:
            {
              date, role, distributor_center,
              metrics: [{code, name, direction, target, trigger, unit}],  # headers de columnas
              personnel: [
                { id, name, code, position_type,
                  values: { <code>: {value, band, target, trigger, ...}, ... } }
              ]
            }
        """
        from apps.personnel.models.personnel import PersonnelProfile
        from apps.truck_cycle.models.core import PautaModel
        from apps.truck_cycle.models.operational import (
            PautaAssignmentModel,
            InconsistencyModel,
        )
        from apps.truck_cycle.models.catalogs import KPITargetModel

        role = (request.query_params.get('role') or '').lower()
        role_map = {
            'picker': {
                'assignment_role': 'PICKER',
                'position_types': ['PICKER', 'LOADER'],
                'metrics': [
                    'picker_pallets_per_hour', 'picker_loads_assembled',
                    'picker_time_per_pauta', 'picker_load_error_rate',
                ],
            },
            'counter': {
                'assignment_role': 'COUNTER',
                'position_types': ['COUNTER', 'WAREHOUSE_ASSISTANT'],
                'metrics': [
                    'counter_pallets_per_hour', 'counter_time_per_truck',
                    'counter_error_rate',
                ],
            },
            'yard': {
                'assignment_role': 'YARD_DRIVER',
                'position_types': ['YARD_DRIVER'],
                'metrics': [
                    'yard_trucks_moved', 'yard_time_park_to_bay',
                    'yard_time_bay_to_park', 'yard_time_total_move',
                ],
            },
        }
        if role not in role_map:
            return Response({'error': 'role requerido: picker|counter|yard'}, status=400)
        spec = role_map[role]

        op_date_str = request.query_params.get('operational_date')
        try:
            op_date = (
                timezone.datetime.fromisoformat(op_date_str).date()
                if op_date_str else timezone.localdate()
            )
        except (TypeError, ValueError):
            op_date = timezone.localdate()

        dc_id = request.query_params.get('distributor_center')
        if not dc_id:
            try:
                dc_id = request.user.centro_distribucion_id
            except Exception:
                dc_id = None

        # Personnel que participaron hoy: por assignment de pauta OR por sample
        # del día. Los samples solos (sin pauta) cubren el caso de demos/backfill
        # o métricas manuales futuras.
        assignments = PautaAssignmentModel.objects.filter(
            role=spec['assignment_role'],
            pauta__operational_date=op_date,
        )
        if dc_id:
            assignments = assignments.filter(pauta__distributor_center_id=dc_id)

        assignment_personnel = set(assignments.values_list('personnel_id', flat=True))

        sample_personnel_qs = PersonnelMetricSample.objects.filter(
            operational_date=op_date,
            metric_type__code__in=spec['metrics'],
        )
        if dc_id:
            sample_personnel_qs = sample_personnel_qs.filter(
                personnel__primary_distributor_center_id=dc_id,
            )
        sample_personnel = set(sample_personnel_qs.values_list('personnel_id', flat=True))

        personnel_ids = list(assignment_personnel | sample_personnel)
        personnel_qs = PersonnelProfile.objects.filter(
            pk__in=personnel_ids,
        ).only('id', 'first_name', 'last_name', 'employee_code', 'position_type')

        # Cache metric types + targets vigentes para el CD.
        mt_map = {
            mt.code: mt for mt in PerformanceMetricType.objects.filter(
                code__in=spec['metrics'], is_active=True,
            )
        }
        targets_by_code = {}
        if dc_id:
            targets_qs = KPITargetModel.objects.filter(
                metric_type__code__in=spec['metrics'],
                distributor_center_id=dc_id,
                effective_from__lte=op_date,
            ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=op_date)).select_related('metric_type')
            for t in targets_qs:
                code = t.metric_type.code
                existing = targets_by_code.get(code)
                if not existing or t.effective_from > existing.effective_from:
                    targets_by_code[code] = t

        # Header de métricas
        metrics_header = []
        for code in spec['metrics']:
            mt = mt_map.get(code)
            target = targets_by_code.get(code)
            metrics_header.append({
                'code': code,
                'name': mt.name if mt else code,
                'unit': (target.unit if target and target.unit else (mt.unit if mt else '')),
                'direction': target.direction if target else None,
                'target': float(target.target_value) if target else None,
                'trigger': float(target.warning_threshold) if (target and target.warning_threshold is not None) else None,
            })

        # Samples del día para todas las personas y métricas relevantes.
        samples = PersonnelMetricSample.objects.filter(
            operational_date=op_date,
            personnel_id__in=personnel_ids,
            metric_type__code__in=spec['metrics'],
        ).values('personnel_id', 'metric_type__code', 'numeric_value')

        # Agregación: por persona → por metric → lista de valores
        agg = {}
        for s in samples:
            pid = s['personnel_id']
            code = s['metric_type__code']
            agg.setdefault(pid, {}).setdefault(code, []).append(float(s['numeric_value']))

        # Pautas-por-persona (para Picker: cargas_assembled, fractions; Counter: total_pallets)
        pautas_by_person = {}
        for pid in personnel_ids:
            ps = PautaModel.objects.filter(
                operational_date=op_date,
                assignments__role=spec['assignment_role'],
                assignments__personnel_id=pid,
            ).distinct()
            if dc_id:
                ps = ps.filter(distributor_center_id=dc_id)
            pautas_by_person[pid] = ps

        # Construir filas por personnel.
        rows = []
        for p in personnel_qs:
            person_agg = agg.get(p.id, {})
            values = {}
            pautas = pautas_by_person.get(p.id)
            for mh in metrics_header:
                code = mh['code']
                sample_values = person_agg.get(code, [])
                value = None

                if role == 'picker':
                    if code == 'picker_time_per_pauta':
                        value = sum(sample_values) / len(sample_values) if sample_values else None
                    elif code == 'picker_loads_assembled':
                        value = pautas.filter(status__in=[
                            'PICKING_DONE', 'MOVING_TO_BAY', 'IN_BAY', 'PENDING_COUNT',
                            'COUNTING', 'COUNTED', 'CHECKOUT_SECURITY', 'CHECKOUT_OPS',
                            'DISPATCHED', 'CLOSED',
                        ]).count() if pautas is not None else 0
                    elif code == 'picker_pallets_per_hour':
                        frac = pautas.aggregate(t=Sum('assembled_fractions'))['t'] or 0 if pautas is not None else 0
                        total_min = sum(sample_values) if sample_values else 0
                        value = (frac / (total_min / 60)) if total_min > 0 else None
                    elif code == 'picker_load_error_rate':
                        if pautas is not None:
                            errs = InconsistencyModel.objects.filter(
                                pauta__in=pautas, phase='VERIFICATION',
                            ).aggregate(t=Sum('difference'))['t'] or 0
                            boxes = pautas.aggregate(t=Sum('total_boxes'))['t'] or 0
                            value = (abs(errs) / boxes * 100) if boxes > 0 else None
                elif role == 'counter':
                    if code == 'counter_time_per_truck':
                        value = sum(sample_values) / len(sample_values) if sample_values else None
                    elif code == 'counter_pallets_per_hour':
                        total_pallets = float(pautas.aggregate(t=Sum('total_pallets'))['t'] or 0) if pautas is not None else 0
                        total_min = sum(sample_values) if sample_values else 0
                        value = (total_pallets / (total_min / 60)) if total_min > 0 else None
                    elif code == 'counter_error_rate':
                        if pautas is not None:
                            errs = InconsistencyModel.objects.filter(
                                pauta__in=pautas, phase='CHECKOUT',
                            ).aggregate(t=Sum('difference'))['t'] or 0
                            boxes = pautas.aggregate(t=Sum('total_boxes'))['t'] or 0
                            value = (abs(errs) / boxes * 100) if boxes > 0 else None
                elif role == 'yard':
                    if code == 'yard_trucks_moved':
                        value = pautas.count() if pautas is not None else 0
                    elif code in ('yard_time_park_to_bay', 'yard_time_bay_to_park', 'yard_time_total_move'):
                        value = sum(sample_values) / len(sample_values) if sample_values else None

                mt_id = mt_map[code].id if code in mt_map else None
                if mt_id is None:
                    values[code] = {'value': None, 'band': 'GRAY', 'target': None, 'trigger': None, 'unit': mh['unit']}
                else:
                    values[code] = band_for(value, mt_id, dc_id, op_date)
                    values[code]['value'] = _round(values[code]['value'])

            rows.append({
                'id': p.id,
                'name': p.full_name,
                'code': p.employee_code,
                'position_type': p.position_type,
                'values': values,
            })

        return Response({
            'date': str(op_date),
            'role': role,
            'distributor_center': int(dc_id) if dc_id else None,
            'metrics': metrics_header,
            'personnel': rows,
        })


def _round(value, digits=2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None
