from rest_framework import serializers
from apps.user.models import PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer para las suscripciones de push notifications
    """
    subscription = serializers.JSONField(write_only=True)

    class Meta:
        model = PushSubscription
        fields = ['id', 'subscription', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        subscription_data = validated_data.pop('subscription')

        # Extraer los datos de la suscripción
        endpoint = subscription_data.get('endpoint')
        keys = subscription_data.get('keys', {})

        # Obtener el usuario del contexto
        user = self.context['request'].user

        # Verificar si ya existe una suscripción para este endpoint
        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': user,
                'auth': keys.get('auth'),
                'p256dh': keys.get('p256dh'),
                'is_active': True
            }
        )

        return subscription


class UnsubscribeSerializer(serializers.Serializer):
    """
    Serializer para desuscribirse de push notifications
    """
    endpoint = serializers.URLField(required=True)
