"""
Helpers para emisión de métricas de Reempaque.

Modelo:
- `repack_boxes_per_hour`: 1 sample por hora HN con entries en esa sesión.
  Los samples se recalculan cada vez que el operario crea/edita/borra un
  entry (incluyendo ajustes negativos con el botón `-`). La columna del
  SIC chart va creciendo o decreciendo en vivo.
- `repack_total_boxes_shift`: 1 sample por sesión, emitido al cerrar
  (`finish`). Refleja el total acumulado del turno.

Cada cambio dispara un `metrics_updated` por WS al grupo del CD para que
las TVs y la pantalla operativa refresquen sin esperar al polling.
"""
from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import Sum
from django.db.models.functions import Extract

from .models import RepackSession


HN_TZ = ZoneInfo('America/Tegucigalpa')


def _broadcast_metrics_updated(dc_id, personnel_id, metric_code):
    """WS event para que TV/pantalla operativa refresque queries del SIC."""
    if not dc_id:
        return
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            f'truck_cycle_cd_{dc_id}',
            {
                'type': 'metrics_updated',
                'metric_code': metric_code,
                'personnel_id': personnel_id,
            },
        )
    except Exception:
        # Channels no configurado o redis caído — no romper el request.
        pass


def recompute_repack_hourly_samples(session: RepackSession) -> int:
    """Reescribe los samples `repack_boxes_per_hour` de esta sesión.

    Borra los samples previos de la sesión (matched por
    `context.repack_session_id`) y crea uno nuevo por cada hora HN con
    entries. `numeric_value = sum(box_count)` de los entries en esa hora.

    El `created_at` del sample se ancla a `HORA:00:00 HN` del
    `operational_date` para que `Extract('hour', tzinfo=HN_TZ)` lo
    mapee exactamente a la columna correspondiente del SIC.

    Devuelve cuántos samples (horas) quedaron escritos.
    """
    try:
        from apps.personnel.models.metric_sample import PersonnelMetricSample
        from apps.personnel.models.performance_new import PerformanceMetricType
    except Exception:
        return 0

    try:
        metric = PerformanceMetricType.objects.get(code='repack_boxes_per_hour')
    except PerformanceMetricType.DoesNotExist:
        return 0

    # Borrar samples previos de esta sesión — siempre reescribimos.
    PersonnelMetricSample.objects.filter(
        personnel=session.personnel,
        metric_type=metric,
        context__repack_session_id=session.id,
    ).delete()

    # Agrupar entries por hora HN. Extract con tzinfo da la hora local del CD.
    by_hour = (
        session.entries
        .annotate(h=Extract('created_at', 'hour', tzinfo=HN_TZ))
        .values('h')
        .annotate(total=Sum('box_count'))
        .order_by('h')
    )

    op_date = session.operational_date
    written = 0
    for row in by_hour:
        hour = int(row['h'])
        total = row['total']
        if total is None:
            continue
        # Si la hora quedó en 0 (ajustes que se cancelan), igual creamos
        # el sample con valor 0 — refleja "el operario hizo movimientos
        # esa hora pero el neto fue 0". Saltamos sólo None.
        anchor = datetime.combine(op_date, time(hour, 0, 0), tzinfo=HN_TZ)
        PersonnelMetricSample.objects.create(
            personnel=session.personnel,
            metric_type=metric,
            operational_date=op_date,
            numeric_value=Decimal(str(total)),
            source=PersonnelMetricSample.SOURCE_AUTO,
            created_at=anchor,
            context={
                'repack_session_id': session.id,
                'hour_hn': hour,
                'boxes_in_hour': int(total),
            },
        )
        written += 1
    return written


def emit_total_shift_sample(session: RepackSession) -> bool:
    """Emite/reescribe el sample `repack_total_boxes_shift` para esta sesión.

    Llamado al cerrar (`finish`). Es el total neto de cajas del turno —
    contempla ajustes negativos. Si la métrica no existe en DB, no falla.
    """
    try:
        from apps.personnel.models.metric_sample import PersonnelMetricSample
        from apps.personnel.models.performance_new import PerformanceMetricType
    except Exception:
        return False

    try:
        metric = PerformanceMetricType.objects.get(code='repack_total_boxes_shift')
    except PerformanceMetricType.DoesNotExist:
        return False

    PersonnelMetricSample.objects.filter(
        personnel=session.personnel,
        metric_type=metric,
        context__repack_session_id=session.id,
    ).delete()

    total = session.total_boxes
    PersonnelMetricSample.objects.create(
        personnel=session.personnel,
        metric_type=metric,
        operational_date=session.operational_date,
        numeric_value=Decimal(str(total)),
        source=PersonnelMetricSample.SOURCE_AUTO,
        context={
            'repack_session_id': session.id,
            'total_boxes': total,
            'duration_seconds': session.duration_seconds,
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
        },
    )
    return True


def on_entry_changed(session: RepackSession) -> None:
    """Hook llamado tras crear/modificar/borrar un entry.

    Re-agrega los samples por hora y dispara WS broadcast para que el SIC
    de la TV/pantalla operativa refresque. Si la sesión no está activa,
    igual recalculamos (puede haber ediciones administrativas post-cierre).
    """
    recompute_repack_hourly_samples(session)
    _broadcast_metrics_updated(
        session.distributor_center_id,
        session.personnel_id,
        'repack_boxes_per_hour',
    )


def on_session_finished(session: RepackSession) -> None:
    """Hook llamado tras `finish`. Asegura el estado por hora final +
    emite el sample agregado del turno + broadcast doble."""
    recompute_repack_hourly_samples(session)
    emit_total_shift_sample(session)
    _broadcast_metrics_updated(
        session.distributor_center_id,
        session.personnel_id,
        'repack_boxes_per_hour',
    )
    _broadcast_metrics_updated(
        session.distributor_center_id,
        session.personnel_id,
        'repack_total_boxes_shift',
    )
