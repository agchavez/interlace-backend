from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.truck_cycle.models.core import PautaModel


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
