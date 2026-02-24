from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.user.models import PushSubscription
from apps.user.serializers import PushSubscriptionSerializer, UnsubscribeSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_to_push(request):
    """
    Endpoint para suscribirse a push notifications
    """
    serializer = PushSubscriptionSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'message': 'Suscripción exitosa',
                'subscription': serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsubscribe_from_push(request):
    """
    Endpoint para desuscribirse de push notifications
    """
    serializer = UnsubscribeSerializer(data=request.data)

    if serializer.is_valid():
        endpoint = serializer.validated_data['endpoint']

        try:
            subscription = PushSubscription.objects.get(
                user=request.user,
                endpoint=endpoint
            )
            subscription.is_active = False
            subscription.save()
            # O puedes eliminarlo completamente:
            # subscription.delete()

            return Response(
                {'message': 'Desuscripción exitosa'},
                status=status.HTTP_200_OK
            )
        except PushSubscription.DoesNotExist:
            return Response(
                {'error': 'Suscripción no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_push_subscriptions(request):
    """
    Obtiene todas las suscripciones activas del usuario
    """
    subscriptions = PushSubscription.objects.filter(
        user=request.user,
        is_active=True
    )
    serializer = PushSubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data)
