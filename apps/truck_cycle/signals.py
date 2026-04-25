import logging
from decimal import Decimal

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apps.truck_cycle.models.core import PautaModel
from apps.truck_cycle.models.operational import PautaTimestampModel

logger = logging.getLogger(__name__)


# Mapea cada evento terminal al code de PerformanceMetricType que alimenta,
# el rol de PautaAssignmentModel que identifica a la persona, y el evento
# que abre la ventana (T_start). Duración siempre se guarda en minutos.
_TIMESTAMP_TO_METRIC = {
    'T1_PICKING_END':       {'code': 'picker_time_per_pauta',   'role': 'PICKER',      'start': 'T0_PICKING_START'},
    'T6_COUNT_END':         {'code': 'counter_time_per_truck',  'role': 'COUNTER',     'start': 'T5_COUNT_START'},
    'T1B_YARD_END':         {'code': 'yard_time_park_to_bay',   'role': 'YARD_DRIVER', 'start': 'T1A_YARD_START'},
    'T8B_YARD_RETURN_END':  {'code': 'yard_time_bay_to_park',   'role': 'YARD_DRIVER', 'start': 'T8A_YARD_RETURN_START'},
}


def _save_sample(personnel, metric_code, operational_date, value, pauta_id, context):
    """Escribe un PersonnelMetricSample si existe el PerformanceMetricType.

    Además emite 'metrics_updated' al WebSocket del CD de la persona, para que
    las pantallas de workstation actualicen en vivo (no hace falta polling).
    """
    from apps.personnel.models.performance_new import PerformanceMetricType
    from apps.personnel.models.metric_sample import PersonnelMetricSample

    try:
        metric_type = PerformanceMetricType.objects.get(code=metric_code, is_active=True)
    except PerformanceMetricType.DoesNotExist:
        # El comando `seed_truck_cycle_metrics` aún no se corrió; silencia.
        return

    PersonnelMetricSample.objects.create(
        personnel=personnel,
        metric_type=metric_type,
        operational_date=operational_date,
        numeric_value=Decimal(str(round(float(value), 4))),
        source=PersonnelMetricSample.SOURCE_AUTO,
        pauta_id=pauta_id,
        context=context or {},
    )

    # Broadcast WS al grupo del CD (no falla si no hay channel layer).
    try:
        dc_id = getattr(personnel, 'primary_distributor_center_id', None)
        if dc_id:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'truck_cycle_cd_{dc_id}',
                    {
                        'type': 'metrics_updated',
                        'metric_code': metric_code,
                        'personnel_id': personnel.id,
                    }
                )
    except Exception:
        pass


@receiver(post_save, sender=PautaTimestampModel)
def on_pauta_timestamp_created(sender, instance, created, **kwargs):
    """Cuando se emite un evento terminal, persistir el sample correspondiente.

    Flujo: busca el T_start de la misma pauta, calcula la duración en
    minutos, identifica al personnel por la última PautaAssignment activa
    con el rol esperado, y escribe un PersonnelMetricSample.
    """
    if not created:
        return

    spec = _TIMESTAMP_TO_METRIC.get(instance.event_type)
    if not spec:
        return

    pauta = instance.pauta
    start_ts = pauta.timestamps.filter(event_type=spec['start']).order_by('timestamp').first()
    if not start_ts:
        return

    minutes = (instance.timestamp - start_ts.timestamp).total_seconds() / 60.0
    if minutes < 0:
        return

    assignment = (
        pauta.assignments
        .filter(role=spec['role'], is_active=True, personnel__isnull=False)
        .order_by('-assigned_at')
        .first()
    )
    if not assignment:
        return

    try:
        _save_sample(
            personnel=assignment.personnel,
            metric_code=spec['code'],
            operational_date=pauta.operational_date,
            value=minutes,
            pauta_id=pauta.id,
            context={
                'event_start': spec['start'],
                'event_end': instance.event_type,
                'transport_number': pauta.transport_number,
            },
        )

        # Tiempo total de movimiento del yard driver = Estac→Bahía + Bahía→Estac.
        if instance.event_type == 'T8B_YARD_RETURN_END':
            t1a = pauta.timestamps.filter(event_type='T1A_YARD_START').order_by('timestamp').first()
            t1b = pauta.timestamps.filter(event_type='T1B_YARD_END').order_by('timestamp').first()
            if t1a and t1b:
                inbound = (t1b.timestamp - t1a.timestamp).total_seconds() / 60.0
                if inbound >= 0:
                    _save_sample(
                        personnel=assignment.personnel,
                        metric_code='yard_time_total_move',
                        operational_date=pauta.operational_date,
                        value=inbound + minutes,
                        pauta_id=pauta.id,
                        context={'transport_number': pauta.transport_number},
                    )
    except Exception as exc:
        logger.exception('Error guardando PersonnelMetricSample (evento %s): %s', instance.event_type, exc)


@receiver(pre_save, sender=PautaModel)
def pauta_pre_save(sender, instance, **kwargs):
    """Marca si el status cambió para emitir broadcast después del save"""
    if not instance.pk:
        return
    try:
        old_status = PautaModel.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
        if old_status and old_status != instance.status:
            instance._status_changed = True
    except Exception:
        pass


@receiver(post_save, sender=PautaModel)
def pauta_post_save(sender, instance, created, **kwargs):
    """Emite WebSocket signal después de guardar si el status cambió"""
    if created or getattr(instance, '_status_changed', False):
        instance._status_changed = False
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            dc_id = instance.distributor_center_id
            if not dc_id:
                return

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'truck_cycle_cd_{dc_id}',
                {
                    'type': 'pauta_updated',
                    'pauta_id': instance.pk,
                    'status': instance.status,
                    'transport_number': instance.transport_number,
                }
            )
        except Exception:
            pass  # No romper el flujo si Redis no está disponible
