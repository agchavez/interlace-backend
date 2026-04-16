"""
URLs del módulo truck_cycle
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.catalog_views import (
    TruckViewSet,
    ProductCatalogViewSet,
    BayViewSet,
    KPITargetViewSet,
)
from .views.core_views import (
    PalletComplexUploadViewSet,
    PautaViewSet,
)
from .views.operational_views import (
    InconsistencyViewSet,
    PautaPhotoViewSet,
    PalletTicketViewSet,
)

router = DefaultRouter()

# Catálogos
router.register(r'truck-cycle-truck', TruckViewSet, basename='truck-cycle-truck')
router.register(r'truck-cycle-product-catalog', ProductCatalogViewSet, basename='truck-cycle-product-catalog')
router.register(r'truck-cycle-bay', BayViewSet, basename='truck-cycle-bay')
router.register(r'truck-cycle-kpi-target', KPITargetViewSet, basename='truck-cycle-kpi-target')

# Core
router.register(r'truck-cycle-upload', PalletComplexUploadViewSet, basename='truck-cycle-upload')
router.register(r'truck-cycle-pauta', PautaViewSet, basename='truck-cycle-pauta')

# Operativos
router.register(r'truck-cycle-inconsistency', InconsistencyViewSet, basename='truck-cycle-inconsistency')
router.register(r'truck-cycle-photo', PautaPhotoViewSet, basename='truck-cycle-photo')
router.register(r'truck-cycle-pallet-ticket', PalletTicketViewSet, basename='truck-cycle-pallet-ticket')

urlpatterns = [
    path('', include(router.urls)),
    path('truck-cycle-public/arrival/<str:truck_code>/',
         PautaViewSet.as_view({'post': 'public_arrival'}),
         name='truck-cycle-public-arrival'),
    path('truck-cycle-public/truck-status/<str:truck_code>/',
         PautaViewSet.as_view({'get': 'public_truck_status'}),
         name='truck-cycle-public-truck-status'),
]
