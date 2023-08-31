from rest_framework import routers
from django.urls import path, re_path, include

# Views
from apps.user.views import UserViewSet, LogEntryViewSet, DetailGroupViewSet

# Routers
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'log', LogEntryViewSet)
router.register(r'groups', DetailGroupViewSet)

