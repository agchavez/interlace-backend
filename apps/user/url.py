from rest_framework import routers
from django.urls import path, re_path, include

# Views
from apps.user.views import UserViewSet, LogEntryViewSet, DetailGroupViewSet
from apps.user.views.notificacion import NotificationViewSet
from apps.user.views import subscribe_to_push, unsubscribe_from_push, get_push_subscriptions

# Routers
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'log', LogEntryViewSet)
router.register(r'groups', DetailGroupViewSet)
router.register(r'notification', NotificationViewSet)

# Push notification URLs
urlpatterns = [
    path('push/subscribe/', subscribe_to_push, name='push-subscribe'),
    path('push/unsubscribe/', unsubscribe_from_push, name='push-unsubscribe'),
    path('push/subscriptions/', get_push_subscriptions, name='push-subscriptions'),
]

