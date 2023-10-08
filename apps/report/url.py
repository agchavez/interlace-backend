from rest_framework import routers
from django.urls import path, re_path, include

# Views
from apps.report.views import ProductosProximosAVencerAPI

# Routers
router = routers.DefaultRouter()
router.register(r'report/next-win', ProductosProximosAVencerAPI, basename='productos-proximos-a-vencer')
