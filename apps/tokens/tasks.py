"""
Tareas de Celery para el módulo de tokens
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task
def expire_old_tokens():
    """
    Marca como expirados los tokens que han pasado su fecha de validez.
    Se ejecuta cada 30 minutos.
    """
    from .models import TokenRequest

    now = timezone.now()

    with transaction.atomic():
        expired_count = TokenRequest.objects.filter(
            status=TokenRequest.Status.APPROVED,
            valid_until__lt=now
        ).update(status=TokenRequest.Status.EXPIRED)

    logger.info(f"Tokens expirados: {expired_count}")
    return f"Expirados: {expired_count}"


@shared_task
def send_pending_approval_reminders():
    """
    Envía recordatorios de tokens pendientes de aprobación.
    Se ejecuta diariamente a las 8 AM.
    """
    from .models import TokenRequest
    from .utils import TokenNotificationHelper

    pending_statuses = [
        TokenRequest.Status.PENDING_L1,
        TokenRequest.Status.PENDING_L2,
        TokenRequest.Status.PENDING_L3,
    ]

    pending_tokens = TokenRequest.objects.filter(
        status__in=pending_statuses
    )

    reminder_count = 0
    for token in pending_tokens:
        TokenNotificationHelper.notify_pending_approval(token)
        reminder_count += 1

    logger.info(f"Recordatorios enviados para {reminder_count} tokens pendientes")
    return f"Recordatorios: {reminder_count}"


@shared_task
def check_tokens_expiring_soon():
    """
    Notifica sobre tokens que expirarán pronto (24 horas).
    Se ejecuta diariamente.
    """
    from .models import TokenRequest
    from .utils import TokenNotificationHelper
    from datetime import timedelta

    now = timezone.now()
    expiring_threshold = now + timedelta(hours=24)

    expiring_tokens = TokenRequest.objects.filter(
        status=TokenRequest.Status.APPROVED,
        valid_until__gt=now,
        valid_until__lte=expiring_threshold
    )

    notified_count = 0
    for token in expiring_tokens:
        hours_remaining = int((token.valid_until - now).total_seconds() / 3600)
        TokenNotificationHelper.notify_token_expiring_soon(token, hours_remaining)
        notified_count += 1

    logger.info(f"Notificados {notified_count} tokens por expirar")
    return f"Por expirar: {notified_count}"


@shared_task
def generate_token_qr_async(token_id):
    """
    Genera el código QR de un token de forma asíncrona.
    """
    from .models import TokenRequest
    from .utils import generate_token_qr

    try:
        token = TokenRequest.objects.get(id=token_id)
        qr_url = generate_token_qr(token)
        token.qr_code_url = qr_url
        token.save(update_fields=['qr_code_url'])
        logger.info(f"QR generado para token {token.display_number}")
        return qr_url
    except TokenRequest.DoesNotExist:
        logger.error(f"Token {token_id} no encontrado")
        return None
    except Exception as e:
        logger.error(f"Error generando QR para token {token_id}: {e}")
        return None
