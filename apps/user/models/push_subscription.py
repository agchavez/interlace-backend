from django.db import models
from django.conf import settings


class PushSubscription(models.Model):
    """
    Modelo para almacenar las suscripciones de push notifications de los usuarios
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500, unique=True)
    auth = models.CharField(max_length=255)
    p256dh = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_push_subscription'
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."

    @property
    def subscription_info(self):
        """Retorna la información de suscripción en formato para pywebpush"""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "auth": self.auth,
                "p256dh": self.p256dh
            }
        }
