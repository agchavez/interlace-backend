from rest_framework import routers
from django.urls import path, re_path, include

# Views
from apps.report.views import ProductosProximosAVencerAPI, TATAPI, DashboardAPI
# Routers
router = routers.DefaultRouter()
router.register(r'report/next-win', ProductosProximosAVencerAPI, basename='productos-proximos-a-vencer')
router.register(r'graph/tat', TATAPI, basename='tat')
router.register(r'dashboard', DashboardAPI, basename='dashboard')
