"""
Utilidades para enviar push notifications usando Web Push Protocol
"""
import json
import logging
from typing import List, Optional, Dict, Any

from django.conf import settings
from apps.user.models import PushSubscription

logger = logging.getLogger(__name__)

# Estas funciones requieren pywebpush instalado
try:
    from pywebpush import webpush, WebPushException
    from py_vapid import Vapid
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logger.warning("pywebpush no está instalado. Las notificaciones push no estarán disponibles.")


def send_push_notification(
    subscription: PushSubscription,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    icon: Optional[str] = None,
    badge: Optional[str] = None,
    tag: Optional[str] = None,
    actions: Optional[List[Dict[str, str]]] = None
) -> bool:
    """
    Envía una push notification a una suscripción específica

    Args:
        subscription: Instancia de PushSubscription
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
        icon: URL del icono (opcional)
        badge: URL del badge (opcional)
        tag: Tag para agrupar notificaciones (opcional)
        actions: Lista de acciones (opcional)

    Returns:
        bool: True si se envió exitosamente, False en caso contrario
    """
    if not WEBPUSH_AVAILABLE:
        logger.error("pywebpush no está disponible")
        return False

    if not subscription.is_active:
        logger.warning(f"Suscripción {subscription.id} no está activa")
        return False

    # Preparar el payload
    payload = {
        "notification": {
            "title": title,
            "body": body,
        }
    }

    if icon:
        payload["notification"]["icon"] = icon
    if badge:
        payload["notification"]["badge"] = badge
    if tag:
        payload["notification"]["tag"] = tag
    if actions:
        payload["notification"]["actions"] = actions
    if data:
        payload["notification"]["data"] = data

    # VAPID claims
    vapid_claims = {
        "sub": f"mailto:{getattr(settings, 'VAPID_ADMIN_EMAIL', 'admin@example.com')}"
    }

    # Cargar VAPID desde archivo
    import os
    vapid_key_path = os.path.join(settings.BASE_DIR, 'vapid_private.pem')

    try:
        vapid = Vapid.from_file(vapid_key_path)

        response = webpush(
            subscription_info=subscription.subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid,
            vapid_claims=vapid_claims
        )

        logger.info(f"Push notification enviada exitosamente a {subscription.user.username}")
        return True

    except WebPushException as e:
        logger.error(f"Error al enviar push notification: {e}")

        # Si la suscripción no es válida, desactivarla
        if e.response and e.response.status_code in [404, 410]:
            logger.info(f"Suscripción {subscription.id} inválida, desactivando...")
            subscription.is_active = False
            subscription.save()

        return False

    except Exception as e:
        logger.error(f"Error inesperado al enviar push notification: {e}")
        return False


def send_push_to_user(
    user,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> int:
    """
    Envía una push notification a todas las suscripciones activas de un usuario

    Args:
        user: Instancia de UserModel
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
        **kwargs: Argumentos adicionales para la notificación (icon, badge, tag, actions)

    Returns:
        int: Número de notificaciones enviadas exitosamente
    """
    subscriptions = PushSubscription.objects.filter(
        user=user,
        is_active=True
    )

    sent_count = 0
    for subscription in subscriptions:
        if send_push_notification(subscription, title, body, data, **kwargs):
            sent_count += 1

    return sent_count


def send_push_to_multiple_users(
    users: List,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> int:
    """
    Envía una push notification a múltiples usuarios

    Args:
        users: Lista de instancias de UserModel
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
        **kwargs: Argumentos adicionales para la notificación

    Returns:
        int: Número total de notificaciones enviadas exitosamente
    """
    total_sent = 0
    for user in users:
        sent = send_push_to_user(user, title, body, data, **kwargs)
        total_sent += sent

    return total_sent


def send_broadcast_notification(
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> int:
    """
    Envía una notificación broadcast a todas las suscripciones activas

    Args:
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
        **kwargs: Argumentos adicionales para la notificación

    Returns:
        int: Número de notificaciones enviadas exitosamente
    """
    subscriptions = PushSubscription.objects.filter(is_active=True)

    sent_count = 0
    for subscription in subscriptions:
        if send_push_notification(subscription, title, body, data, **kwargs):
            sent_count += 1

    return sent_count
