"""
Helper para enviar notificaciones relacionadas con tokens
"""
import logging
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.user.models import NotificationModel
from apps.user.serializers.notificacion import NotificationSerializer
from apps.personnel.models import PersonnelProfile

# Push notifications
try:
    from apps.user.utils.push_notifications import send_push_to_user
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Labels en español para tipos de token
TOKEN_TYPE_LABELS = {
    'PERMIT_HOUR': 'Permiso por Hora',
    'PERMIT_DAY': 'Permiso por Día',
    'EXIT_PASS': 'Pase de Salida',
    'UNIFORM_DELIVERY': 'Entrega de Uniforme',
    'SUBSTITUTION': 'Sustitución',
    'RATE_CHANGE': 'Cambio de Tasa',
    'OVERTIME': 'Horas Extra',
    'SHIFT_CHANGE': 'Cambio de Turno',
}


def get_token_type_label(token_type):
    """Obtiene la etiqueta en español del tipo de token"""
    return TOKEN_TYPE_LABELS.get(token_type, token_type)


class TokenNotificationHelper:
    """
    Clase helper para gestionar notificaciones de tokens.
    Integra con el sistema existente de notificaciones:
    - Base de datos (NotificationModel)
    - WebSocket (tiempo real en navegador)
    - Push Notifications (dispositivos móviles y navegadores)
    """

    @classmethod
    def _send_websocket_notification(cls, user_id, notification):
        """Envía notificación por WebSocket"""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                str(user_id),
                {
                    'type': 'send_notification',
                    'data': NotificationSerializer(notification).data
                }
            )
        except Exception as e:
            logger.error(f"Error enviando WebSocket notification: {e}")

    @classmethod
    def _send_push_notification(cls, user, title, body, url=None, token_data=None):
        """Envía notificación push al usuario si tiene suscripciones activas"""
        if not PUSH_AVAILABLE:
            return 0

        try:
            data = {
                'url': url,
                'module': 'tokens',
            }
            if token_data:
                data.update(token_data)

            sent_count = send_push_to_user(
                user=user,
                title=title,
                body=body,
                data=data,
                tag=f"token-{token_data.get('token_id', 'unknown')}" if token_data else None
            )
            if sent_count > 0:
                logger.info(f"Push notification enviada a {user.username} ({sent_count} dispositivos)")
            return sent_count
        except Exception as e:
            logger.error(f"Error enviando push notification: {e}")
            return 0

    @classmethod
    def _create_notification(cls, user, title, description, token, notification_type):
        """Crea una notificación en la base de datos y la envía por WebSocket y Push"""
        try:
            token_type_label = get_token_type_label(token.token_type)
            token_data = {
                'token_id': token.id,
                'token_type': token.token_type,
                'token_type_label': token_type_label,
                'display_number': token.display_number,
            }
            url = f'/tokens/detail/{token.id}'

            notification = NotificationModel.objects.create(
                user=user,
                type=notification_type,
                title=title,
                subtitle=f"{token_type_label} - {token.display_number}",
                description=description,
                module=NotificationModel.Modules.TOKENS,
                url=url,
                identifier=token.id,
                json=token_data
            )

            # Enviar por WebSocket
            cls._send_websocket_notification(user.id, notification)

            # Enviar por Push Notification
            cls._send_push_notification(
                user=user,
                title=title,
                body=description,
                url=url,
                token_data=token_data
            )

            return notification
        except Exception as e:
            logger.error(f"Error creando notificación: {e}")
            return None

    @classmethod
    def notify_pending_approval(cls, token):
        """
        Notifica que hay un token pendiente de aprobación.
        Envía notificación a los aprobadores del nivel actual.
        """
        current_level = token.get_current_approval_level()
        if not current_level:
            return

        # Determinar qué aprobadores notificar según el nivel
        level_map = {
            1: 'can_approve_tokens_level_1',
            2: 'can_approve_tokens_level_2',
            3: 'can_approve_tokens_level_3',
        }

        level_names = {
            1: 'Supervisor',
            2: 'Jefe de Área',
            3: 'Gerente CD',
        }

        # Obtener personal que puede aprobar en el nivel actual
        # Filtrar por mismo centro de distribución
        approvers = PersonnelProfile.objects.filter(
            is_active=True,
            user__isnull=False,
            user__is_active=True,
        ).exclude(
            id=token.personnel.id  # Excluir al beneficiario
        )

        # Filtrar por centro de distribución
        approvers = approvers.filter(
            primary_distributor_center=token.distributor_center
        ) | approvers.filter(
            distributor_centers=token.distributor_center
        )

        approvers = approvers.distinct()

        token_type_label = get_token_type_label(token.token_type)
        level_name = level_names.get(current_level, f'Nivel {current_level}')

        # Filtrar por capacidad de aprobación
        notified_count = 0
        for approver in approvers:
            method_name = level_map.get(current_level)
            if method_name and getattr(approver, method_name)():
                if approver.user:
                    cls._create_notification(
                        user=approver.user,
                        title=f"Solicitud pendiente de aprobación",
                        description=f"{token.personnel.full_name} solicita {token_type_label}. Requiere su aprobación como {level_name}.",
                        token=token,
                        notification_type=NotificationModel.Type.APROVAL,
                    )
                    notified_count += 1

        logger.info(f"Notificados {notified_count} aprobadores para token {token.display_number}")

    @classmethod
    def notify_token_approved(cls, token, level):
        """
        Notifica que un token fue aprobado en un nivel específico.

        Lógica de notificaciones:
        - Solo notificar al BENEFICIARIO sobre el progreso de su token
        - Solo notificar al SOLICITANTE si es diferente al beneficiario
        - Los aprobadores NO reciben notificación de aprobaciones de otros niveles
        """
        token_type_label = get_token_type_label(token.token_type)
        level_names = {
            1: 'Supervisor',
            2: 'Jefe de Área',
            3: 'Gerente CD',
        }
        level_name = level_names.get(level, f'Nivel {level}')

        # Si está completamente aprobado
        if token.status == 'APPROVED':
            # Notificar al beneficiario si tiene usuario
            if token.personnel.user:
                cls._create_notification(
                    user=token.personnel.user,
                    title=f"Su {token_type_label} fue aprobado",
                    description=f"Su solicitud ha sido aprobada completamente y está lista para usar.",
                    token=token,
                    notification_type=NotificationModel.Type.CONFIRMATION,
                )

            # Notificar al solicitante SOLO si es diferente al beneficiario
            if token.requested_by and token.requested_by != token.personnel.user:
                cls._create_notification(
                    user=token.requested_by,
                    title=f"Solicitud aprobada completamente",
                    description=f"La solicitud de {token_type_label} para {token.personnel.full_name} ha sido aprobada y está lista para usar.",
                    token=token,
                    notification_type=NotificationModel.Type.CONFIRMATION,
                )
        else:
            # Aprobación parcial - solo notificar al beneficiario si tiene usuario
            # El beneficiario quiere saber el progreso de su solicitud
            if token.personnel.user:
                cls._create_notification(
                    user=token.personnel.user,
                    title=f"Solicitud aprobada por {level_name}",
                    description=f"Su {token_type_label} ha sido aprobado por {level_name}. Pendiente de aprobación siguiente.",
                    token=token,
                    notification_type=NotificationModel.Type.CONFIRMATION,
                )

    @classmethod
    def notify_token_rejected(cls, token):
        """
        Notifica que un token fue rechazado.
        """
        token_type_label = get_token_type_label(token.token_type)
        rejection_reason = token.rejection_reason or 'No especificado'

        # Notificar al solicitante
        cls._create_notification(
            user=token.requested_by,
            title="Solicitud rechazada",
            description=f"La solicitud de {token_type_label} para {token.personnel.full_name} fue rechazada. Motivo: {rejection_reason}",
            token=token,
            notification_type=NotificationModel.Type.REJECTION,
        )

        # Notificar al beneficiario si tiene usuario y no es el solicitante
        if token.personnel.user and token.personnel.user != token.requested_by:
            cls._create_notification(
                user=token.personnel.user,
                title=f"Su {token_type_label} fue rechazado",
                description=f"Su solicitud fue rechazada. Motivo: {rejection_reason}",
                token=token,
                notification_type=NotificationModel.Type.REJECTION,
            )

    @classmethod
    def notify_token_used(cls, token):
        """
        Notifica que un token fue utilizado (validado por Seguridad).

        Solo notifica al beneficiario. El solicitante solo es notificado
        si es diferente al beneficiario.
        """
        token_type_label = get_token_type_label(token.token_type)

        # Notificar al beneficiario si tiene usuario
        if token.personnel.user:
            cls._create_notification(
                user=token.personnel.user,
                title=f"Su {token_type_label} ha sido utilizado",
                description=f"Su solicitud ha sido validada y registrada en el sistema.",
                token=token,
                notification_type=NotificationModel.Type.CONFIRMATION,
            )

        # Notificar al solicitante SOLO si es diferente al beneficiario
        if token.requested_by and token.requested_by != token.personnel.user:
            cls._create_notification(
                user=token.requested_by,
                title="Solicitud utilizada",
                description=f"La solicitud de {token_type_label} de {token.personnel.full_name} ha sido validada y registrada.",
                token=token,
                notification_type=NotificationModel.Type.CONFIRMATION,
            )

    @classmethod
    def notify_token_expiring_soon(cls, token, hours_remaining):
        """
        Notifica que un token está por expirar.
        """
        token_type_label = get_token_type_label(token.token_type)

        if token.personnel.user:
            cls._create_notification(
                user=token.personnel.user,
                title="Solicitud por vencer",
                description=f"Su {token_type_label} vencerá en {hours_remaining} horas. Utilícelo antes de que expire.",
                token=token,
                notification_type=NotificationModel.Type.WARNING,
            )
