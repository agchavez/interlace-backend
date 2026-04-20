"""
Tareas Celery del ciclo del camión.
"""
import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone


logger = logging.getLogger(__name__)

# Estados considerados "finales" — no se auto-cierran.
FINAL_STATUSES = {'CLOSED', 'CANCELLED'}


@shared_task(name='truck_cycle.close_expired_pautas')
def close_expired_pautas():
    """
    Cierra automáticamente las pautas cuyo `operational_date` es anterior a hoy
    y que aún no están en estado final. Libera la bahía si estaba asignada y
    registra el timestamp T16_CLOSE con nota de cierre automático.

    Se programa para correr todos los días a las 00:00 (America/Tegucigalpa).
    """
    from apps.truck_cycle.models.core import PautaModel
    from apps.truck_cycle.models.operational import PautaTimestampModel

    today = timezone.localdate()
    now = timezone.now()

    qs = PautaModel.objects.filter(
        operational_date__lt=today,
    ).exclude(status__in=FINAL_STATUSES).select_related('bay_assignment')

    total = qs.count()
    if total == 0:
        logger.info('close_expired_pautas: no hay pautas expiradas para cerrar.')
        return {'closed': 0, 'date': str(today)}

    closed_ids = []
    with transaction.atomic():
        for pauta in qs:
            previous_status = pauta.status
            pauta.status = 'CLOSED'
            pauta.save(update_fields=['status'])

            # Liberar la bahía si seguía asignada.
            bay_assignment = getattr(pauta, 'bay_assignment', None)
            if bay_assignment and not bay_assignment.released_at:
                bay_assignment.released_at = now
                bay_assignment.save(update_fields=['released_at'])

            PautaTimestampModel.objects.create(
                event_type='T16_CLOSE',
                pauta=pauta,
                notes=(
                    f'Cerrada automáticamente por el sistema. '
                    f'Fecha operativa {pauta.operational_date} ya pasó. '
                    f'Estado previo: {previous_status}.'
                ),
            )
            closed_ids.append(pauta.id)

    logger.info(
        'close_expired_pautas: cerradas %s pautas (fecha operativa < %s). IDs: %s',
        len(closed_ids), today, closed_ids,
    )
    return {'closed': len(closed_ids), 'date': str(today), 'pauta_ids': closed_ids}
