# Django
from django.db import models

from utils import BaseModel
# Local import
from .user import UserModel

"""
Notification model for users in different modules
"""
class NotificationModel(BaseModel):
    class Meta:
        db_table = "notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    class Type(models.TextChoices):
        LOCATION = 'UBICACION'
        ALERT = 'ALERTA'
        REMINDER = 'RECORDATORIO'
        TASK = 'TAREA'
        UPDATE = 'ACTUALIZACION'
        WARNING = 'ADVERTENCIA'
        INFO = 'INFORMACION'
        ERROR = 'ERROR'
        REGISTRATION = 'REGISTRO'
        APROVAL = 'APROBACION'
        CONFIRMATION = 'CONFIRMACION'
        REJECTION = 'RECHAZO'

    # Application modules
    class Modules(models.TextChoices):
        T1 = 'T1'
        T2 = 'T2'
        CLAIM = 'RECLAMO'
        TRACKER = 'TRACKER'
        USER = 'USUARIO'
        PRODUCT = 'PRODUCTO'
        OTHERS = 'OTROS'

    # The user to whom the notification is sent
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='user_notification')

    # Notification type
    type = models.CharField(max_length=75, null=False, choices=Type.choices)

    # Notification title
    title = models.CharField(max_length=150, null=False)

    subtitle = models.CharField(max_length=150, null=True)

    # Notification description
    description = models.TextField(null=False)

    # Read
    read = models.BooleanField(default=False)

    # Notification identifier
    identifier = models.IntegerField(null=True)

    # Notification URL
    url = models.CharField(max_length=150, null=True)

    # Notification module
    module = models.CharField(max_length=75, null=False, choices=Modules.choices)

    # JSON data for the notification
    json = models.JSONField(null=True)

    # HTML content for the notification if needed
    html = models.TextField(null=True)

    def __str__(self):
        return self.title
