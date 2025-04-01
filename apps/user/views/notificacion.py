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

    permission_classes = [CustomAccessPermission]
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
