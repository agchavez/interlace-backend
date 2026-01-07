"""
Management command to create test notifications for development and testing.

Usage:
    python manage.py create_test_notifications --user 1 --count 5
    python manage.py create_test_notifications --user 1 --type ALERT
    python manage.py create_test_notifications --all-users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.user.models.notificacion import NotificationModel
from apps.user.serializers.notificacion import NotificationSerializer
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test notifications for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='User ID to send notifications to',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of notifications to create (default: 1)',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=[choice[0] for choice in NotificationModel.Type.choices],
            help='Specific notification type',
        )
        parser.add_argument(
            '--module',
            type=str,
            choices=[choice[0] for choice in NotificationModel.Modules.choices],
            help='Specific notification module',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Create notifications for all active users',
        )
        parser.add_argument(
            '--variety',
            action='store_true',
            help='Create a variety of notification types',
        )

    def handle(self, *args, **options):
        user_id = options.get('user')
        count = options.get('count')
        notification_type = options.get('type')
        module = options.get('module')
        all_users = options.get('all_users')
        variety = options.get('variety')

        # Get users
        if all_users:
            users = User.objects.filter(is_active=True)
            self.stdout.write(self.style.SUCCESS(f'Found {users.count()} active users'))
        elif user_id:
            try:
                users = [User.objects.get(id=user_id)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            self.stdout.write(self.style.ERROR('Please specify --user or --all-users'))
            return

        # Notification templates
        templates = self._get_notification_templates()

        created_count = 0
        for user in users:
            for i in range(count):
                if variety:
                    # Random type and module
                    template = random.choice(templates)
                else:
                    # Use specified type or random
                    if notification_type:
                        template = next(
                            (t for t in templates if t['type'] == notification_type),
                            random.choice(templates)
                        )
                    else:
                        template = random.choice(templates)

                # Override module if specified
                if module:
                    template['module'] = module

                # Create notification
                notification = NotificationModel.objects.create(
                    user=user,
                    type=template['type'],
                    title=template['title'].format(user=user.first_name or user.username),
                    subtitle=template['subtitle'],
                    description=template['description'],
                    module=template['module'],
                    url=template.get('url'),
                    identifier=template.get('identifier'),
                    json=template.get('json', {}),
                    html=template.get('html'),
                )

                # Send via WebSocket
                self._send_websocket_notification(user, notification)

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created notification #{notification.id} for user {user.username} ({user.id})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Successfully created {created_count} test notification(s)'
            )
        )

    def _send_websocket_notification(self, user, notification):
        """Send notification via WebSocket to connected clients"""
        try:
            group_name = str(user.id)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'data': NotificationSerializer(notification).data
                }
            )
            self.stdout.write(f'  → WebSocket notification sent to group "{group_name}"')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'  ⚠ WebSocket send failed: {str(e)}')
            )

    def _get_notification_templates(self):
        """Get various notification templates for testing"""
        return [
            {
                'type': NotificationModel.Type.INFO,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Bienvenido al sistema, {user}',
                'subtitle': 'Tu cuenta ha sido configurada correctamente',
                'description': 'Hola {user}, tu cuenta ha sido configurada y está lista para usar. Puedes comenzar a explorar todas las funcionalidades del sistema.',
                'url': '/dashboard',
                'json': {
                    'welcome': True,
                    'timestamp': str(timezone.now()),
                }
            },
            {
                'type': NotificationModel.Type.ALERT,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Alerta: Inventario bajo',
                'subtitle': 'Productos con stock crítico',
                'description': 'Se han detectado 5 productos con niveles de inventario por debajo del mínimo establecido. Se recomienda revisar y reabastecer.',
                'url': '/inventory',
                'json': {
                    'products': ['Producto A', 'Producto B', 'Producto C'],
                    'critical_level': 10,
                    'current_stock': 5,
                }
            },
            {
                'type': NotificationModel.Type.WARNING,
                'module': NotificationModel.Modules.USER,
                'title': 'Advertencia de seguridad',
                'subtitle': 'Tu contraseña expirará pronto',
                'description': 'Tu contraseña actual expirará en 7 días. Por favor, actualízala para mantener tu cuenta segura.',
                'url': '/profile/security',
                'json': {
                    'days_until_expiry': 7,
                    'security_level': 'medium',
                }
            },
            {
                'type': NotificationModel.Type.CONFIRMATION,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Pedido confirmado',
                'subtitle': 'Tu pedido #12345 ha sido procesado',
                'description': 'Tu pedido ha sido confirmado y está en proceso de preparación. Recibirás una actualización cuando esté listo para envío.',
                'url': '/orders/12345',
                'identifier': 12345,
                'json': {
                    'order_id': 12345,
                    'status': 'confirmed',
                    'items_count': 8,
                    'total': 1250.50,
                }
            },
            {
                'type': NotificationModel.Type.TASK,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Nueva tarea asignada',
                'subtitle': 'Revisión de documentos pendiente',
                'description': 'Se te ha asignado una nueva tarea: Revisar y aprobar los documentos de importación del lote #789. Fecha límite: Mañana.',
                'url': '/tasks/456',
                'identifier': 456,
                'json': {
                    'task_id': 456,
                    'priority': 'high',
                    'due_date': str(timezone.now() + timezone.timedelta(days=1)),
                }
            },
            {
                'type': NotificationModel.Type.UPDATE,
                'module': NotificationModel.Modules.PRODUCT,
                'title': 'Actualización de producto',
                'subtitle': 'Precio actualizado para SKU-12345',
                'description': 'El precio del producto "Widget Premium" ha sido actualizado de $99.99 a $89.99. Los cambios son efectivos inmediatamente.',
                'url': '/products/12345',
                'identifier': 12345,
                'json': {
                    'product_id': 12345,
                    'old_price': 99.99,
                    'new_price': 89.99,
                    'sku': 'SKU-12345',
                }
            },
            {
                'type': NotificationModel.Type.REMINDER,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Recordatorio: Reunión programada',
                'subtitle': 'Reunión de equipo en 1 hora',
                'description': 'Recordatorio: Tienes una reunión de equipo programada para las 3:00 PM. Tema: Revisión mensual de métricas.',
                'url': '/calendar',
                'json': {
                    'meeting_time': str(timezone.now() + timezone.timedelta(hours=1)),
                    'attendees': 5,
                    'location': 'Sala de conferencias A',
                }
            },
            {
                'type': NotificationModel.Type.ERROR,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Error en procesamiento',
                'subtitle': 'Fallo en sincronización de datos',
                'description': 'Se detectó un error durante la sincronización automática de datos. El proceso se reintentará automáticamente. Si el problema persiste, contacta a soporte.',
                'url': '/system/logs',
                'json': {
                    'error_code': 'SYNC_ERR_001',
                    'retry_count': 2,
                    'next_retry': str(timezone.now() + timezone.timedelta(minutes=15)),
                }
            },
            {
                'type': NotificationModel.Type.REGISTRATION,
                'module': NotificationModel.Modules.USER,
                'title': 'Nuevo usuario registrado',
                'subtitle': 'Juan Pérez se ha unido al equipo',
                'description': 'Un nuevo miembro del equipo ha sido registrado en el sistema. Nombre: Juan Pérez, Departamento: Logística.',
                'url': '/users/789',
                'identifier': 789,
                'json': {
                    'user_id': 789,
                    'department': 'Logística',
                    'role': 'Operador',
                }
            },
            {
                'type': NotificationModel.Type.APROVAL,
                'module': NotificationModel.Modules.TRACKER,
                'title': 'Aprobación requerida',
                'subtitle': 'Solicitud de vacaciones pendiente',
                'description': 'María González ha solicitado vacaciones del 15 al 22 de marzo. Revisa y aprueba la solicitud.',
                'url': '/approvals/pending',
                'json': {
                    'request_type': 'vacation',
                    'employee': 'María González',
                    'start_date': '2026-03-15',
                    'end_date': '2026-03-22',
                }
            },
            {
                'type': NotificationModel.Type.REJECTION,
                'module': NotificationModel.Modules.CLAIM,
                'title': 'Solicitud rechazada',
                'subtitle': 'Reclamo #456 no aprobado',
                'description': 'Tu reclamo #456 ha sido revisado y no fue aprobado. Motivo: Documentación incompleta. Puedes volver a enviar con la información faltante.',
                'url': '/claims/456',
                'identifier': 456,
                'json': {
                    'claim_id': 456,
                    'reason': 'Documentación incompleta',
                    'can_resubmit': True,
                }
            },
            {
                'type': NotificationModel.Type.CLAIM,
                'module': NotificationModel.Modules.CLAIM,
                'title': 'Nuevo reclamo recibido',
                'subtitle': 'Reclamo #999 requiere atención',
                'description': 'Se ha recibido un nuevo reclamo que requiere tu atención. Cliente: Empresa ABC, Motivo: Producto dañado en tránsito.',
                'url': '/claims/999',
                'identifier': 999,
                'json': {
                    'claim_id': 999,
                    'client': 'Empresa ABC',
                    'reason': 'Producto dañado',
                    'priority': 'high',
                }
            },
            {
                'type': NotificationModel.Type.LOCATION,
                'module': NotificationModel.Modules.T2,
                'title': 'Ubicación actualizada',
                'subtitle': 'Paquete en tránsito - Nuevo checkpoint',
                'description': 'Tu paquete #T2-54321 ha pasado por un nuevo checkpoint. Ubicación actual: Centro de Distribución Lima. Llegada estimada: Mañana.',
                'url': '/tracking/T2-54321',
                'identifier': 54321,
                'json': {
                    'tracking_number': 'T2-54321',
                    'location': 'Centro de Distribución Lima',
                    'status': 'in_transit',
                    'eta': str(timezone.now() + timezone.timedelta(days=1)),
                },
                'html': '<p><strong>Ruta del paquete:</strong></p><ul><li>✓ Origen (Ayer)</li><li>✓ Hub Principal (Hoy 8:00 AM)</li><li><strong>→ CD Lima (Hoy 2:00 PM)</strong></li><li>Destino (Mañana)</li></ul>'
            },
        ]
