from rest_framework import routers
from django.urls import path, re_path, include

# Views
from apps.document.view.document import DocumentViewSet

# Routers
router = routers.DefaultRouter()

router.register(r"document", DocumentViewSet)

