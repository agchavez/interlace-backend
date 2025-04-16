from rest_framework import routers
from django.urls import path, re_path, include

# Views
from apps.imported.view.calim import ClaimViewSet, ClaimProductViewSet, ClaimTypeViewSet

# Routers
router = routers.DefaultRouter()

router.register(r"claim", ClaimViewSet)
router.register(r"claim-product", ClaimProductViewSet)
router.register(r"claim-type", ClaimTypeViewSet)

