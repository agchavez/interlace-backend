# Rest_framework
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter


from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from rest_framework.filters import OrderingFilter

from apps.user.models.notificacion import NotificationModel
from apps.user.serializers.notificacion import NotificationSerializer
from apps.user.views.user import CustomAccessPermission

from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import get_user_model

class NotificationFilter(django_filters.FilterSet):
    class Meta:
        model = NotificationModel
        fields = {
            "read": ["exact"],
            'user': ['exact'],
            "created_at": ["exact", "gte", "lte"],
        }


class NotificationViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet,
                          mixins.RetrieveModelMixin):
    queryset = NotificationModel.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = []
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = NotificationFilter
    ordering_fields = ["created_at"]
    search_fields = ["title", "description", "subtitle"]
    ordering = ["-created_at"]

    permission_classes = []
    # Mapping of HTTP methods to required permissions
    PERMISSION_MAPPING = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': []
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    @action(detail=True, methods=['post'], url_path='mark_read', url_name='mark_read', permission_classes=[IsAuthenticated])
    def mark_read(self, request, pk=None):
        user = request.user
        notification = self.get_object()
        if notification.user != user:
            return Response({"detail": "You do not have permission to mark this notification as read."}, status=403)
        notification.read = True
        notification.save()

        group_name = f"{user.id}"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification_read',
                'data': {
                    "id": notification.id
                }
            }
        )
        data = NotificationSerializer(notification).data
        return Response(data)

    # Mark all notifications as read
    @action(detail=False, methods=['post'], url_path='mark_all_read', url_name='mark_all_read', permission_classes=[IsAuthenticated])
    def mark_all_read(self, request):
        user = request.user
        notifications = NotificationModel.objects.filter(user=user, read=False)
        notifications.update(read=True)
        group_name = f"{user.id}"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notifications_read'
            }
        )
        data = NotificationSerializer(notifications, many=True).data
        return Response(data)

    # retrieve
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.read = True
        instance.save()
        serializer = self.get_serializer(instance)

        group_name = f"{request.user.id}"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification_read',
                'data': {
                    "id": instance.id
                }
            }
        )

        return Response(serializer.data)

    @action(detail=False, methods=['post', 'get'], url_path='test', url_name='test_notification')
    def test_notification(self, request):
        """
        Endpoint para probar el sistema de notificaciones en tiempo real.

        POST /api/notification/test/
        {
            "user_id": 1,
            "title": "Prueba de notificación",
            "subtitle": "Subtítulo de prueba",
            "description": "Esta es una notificación de prueba",
            "type": "INFORMACION",
            "module": "TRACKER",
            "url": "/dashboard",
            "identifier": 123,
            "json_data": {"custom": "data"},
            "html": "<p>Contenido HTML opcional</p>"
        }

        GET /api/notification/test/?user_id=1
        """
        # Soportar tanto GET como POST
        if request.method == 'GET':
            user_id = request.query_params.get('user_id')
            data = {}
        else:
            user_id = request.data.get('user_id')
            data = request.data

        # Validar user_id
        if not user_id:
            return Response(
                {"error": "El campo 'user_id' es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response(
                {"error": f"Usuario con ID {user_id} no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar tipo de notificación
        notification_type = data.get('type', NotificationModel.Type.INFO)
        if notification_type not in dict(NotificationModel.Type.choices):
            return Response(
                {
                    "error": f"Tipo de notificación inválido: {notification_type}",
                    "valid_types": [choice[0] for choice in NotificationModel.Type.choices]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar módulo
        module = data.get('module', NotificationModel.Modules.TRACKER)
        if module not in dict(NotificationModel.Modules.choices):
            return Response(
                {
                    "error": f"Módulo inválido: {module}",
                    "valid_modules": [choice[0] for choice in NotificationModel.Modules.choices]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear notificación
        notification = NotificationModel.objects.create(
            user=user,
            type=notification_type,
            identifier=data.get('identifier'),
            title=data.get('title', 'Notificación de prueba'),
            subtitle=data.get('subtitle', 'Subtítulo de prueba'),
            description=data.get('description', 'Esta es una notificación generada para pruebas del sistema'),
            module=module,
            url=data.get('url', '/dashboard'),
            html=data.get('html'),
            json={
                'test': True,
                'timestamp': str(timezone.now()),
                'method': request.method,
                'data': data.get('json_data', {})
            }
        )

        # Enviar notificación a través de websocket
        group_name = str(user.id)
        channel_layer = get_channel_layer()

        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'data': NotificationSerializer(notification).data
                }
            )
            websocket_sent = True
        except Exception as e:
            websocket_sent = False
            error_message = str(e)

        # Preparar respuesta
        response_data = NotificationSerializer(notification).data
        response_data['websocket_sent'] = websocket_sent
        if not websocket_sent:
            response_data['websocket_error'] = error_message

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )
