# Rest_framework
from rest_framework import serializers

from apps.user.models.notificacion import NotificationModel

# Models

#NotificacionSerializer

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationModel
        fields = '__all__'