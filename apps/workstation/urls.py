"""URLs del módulo Workstation."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ProhibitionCatalogViewSet,
    RiskCatalogViewSet,
    WorkstationBlockViewSet,
    WorkstationDocumentDownloadView,
    WorkstationDocumentMetaView,
    WorkstationDocumentViewSet,
    WorkstationImageViewSet,
    WorkstationViewSet,
)

router = DefaultRouter()
router.register('workstations', WorkstationViewSet, basename='workstation')
router.register('workstation-blocks', WorkstationBlockViewSet, basename='ws-blocks')
router.register('workstation-documents', WorkstationDocumentViewSet, basename='ws-documents')
router.register('workstation-images', WorkstationImageViewSet, basename='ws-images')
router.register('workstation-risk-catalog', RiskCatalogViewSet, basename='ws-risk-catalog')
router.register('workstation-prohibition-catalog', ProhibitionCatalogViewSet, basename='ws-prohibition-catalog')

extra_urlpatterns = [
    path('workstation-doc/<uuid:qr_token>/', WorkstationDocumentMetaView.as_view(), name='ws-doc-meta'),
    path('workstation-doc/<uuid:qr_token>/file/', WorkstationDocumentDownloadView.as_view(), name='ws-doc-file'),
]
