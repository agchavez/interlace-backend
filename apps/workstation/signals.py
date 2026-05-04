"""
Signals del módulo Workstation: notifica a las TVs cuando algo cambia.

Eventos:
  - WorkstationBlock save/delete   → workstation.config.updated  (CD del bloque)
  - WorkstationDocument save/delete → workstation.config.updated  (CD del doc)
  - WorkstationImage save/delete    → workstation.config.updated  (CD de la imagen)
  - KPITargetModel save/delete      → workstation.config.updated  (CD del target)

Cada TV pareada al CD afectado recibe el evento por su canal `tv_session_<code>`.
La TV refetcha el endpoint `/api/tv/sessions/workstation/` y se actualiza.
"""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import WorkstationBlock, WorkstationDocument, WorkstationImage

logger = logging.getLogger(__name__)


def _broadcast_to_cd(distributor_center_id: int | None, payload: dict) -> None:
    """Notifica a todas las TVs PAIRED del CD indicado.

    Si Redis está caído o no responde, **no bloquea** la operación de BD —
    solo loguea el warning y sigue. Esto evita que un Redis inaccesible
    haga colgar transacciones (signals corren dentro del DELETE/UPDATE).
    """
    if not distributor_center_id:
        return
    # Import local para evitar ciclos al cargar la app
    from apps.tv.models import TvSession

    layer = get_channel_layer()
    if not layer:
        return

    try:
        codes = list(TvSession.objects.filter(
            distributor_center_id=distributor_center_id,
            status='PAIRED',
        ).values_list('code', flat=True))
    except Exception as e:
        logger.warning('No se pudieron leer TvSessions para broadcast: %s', e)
        return

    for code in codes:
        try:
            async_to_sync(layer.group_send)(
                f'tv_session_{code}',
                {'type': 'workstation.config.updated', 'data': payload},
            )
        except Exception as e:
            # Redis caído / timeout → no bloquear la transacción de BD.
            logger.warning('Broadcast a tv_session_%s falló (Redis?): %s', code, e)
            return  # si el primero falló, los demás también — abort silencioso


def _cd_for(instance) -> int | None:
    ws = getattr(instance, 'workstation', None)
    return ws.distributor_center_id if ws else None


@receiver([post_save, post_delete], sender=WorkstationBlock)
def workstation_block_changed(sender, instance, **kwargs):
    _broadcast_to_cd(_cd_for(instance), {'reason': 'block', 'block_id': instance.id})


@receiver([post_save, post_delete], sender=WorkstationDocument)
def workstation_document_changed(sender, instance, **kwargs):
    _broadcast_to_cd(_cd_for(instance), {'reason': 'document', 'doc_id': instance.id})


@receiver([post_save, post_delete], sender=WorkstationImage)
def workstation_image_changed(sender, instance, **kwargs):
    _broadcast_to_cd(_cd_for(instance), {'reason': 'image', 'image_id': instance.id})


# KPITargetModel — se importa el modelo en la conexión del signal por si Truck Cycle no está cargado todavía.
def _connect_kpi_target_signal():
    try:
        from apps.truck_cycle.models.catalogs import KPITargetModel
    except Exception:
        return

    @receiver([post_save, post_delete], sender=KPITargetModel, weak=False, dispatch_uid='workstation_kpi_target_changed')
    def kpi_target_changed(sender, instance, **kwargs):
        _broadcast_to_cd(
            instance.distributor_center_id,
            {'reason': 'kpi_target', 'kpi_id': instance.id},
        )


_connect_kpi_target_signal()
