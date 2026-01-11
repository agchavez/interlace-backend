"""
URLs para el módulo de tokens
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TokenRequestViewSet,
    ExternalPersonViewSet,
    MaterialViewSet,
    UnitOfMeasureViewSet,
    public_token_detail,
    public_token_by_code,
    public_token_verify,
    public_token_pdf,
)

router = DefaultRouter()
# Catalogos (rutas especificas primero)
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'units', UnitOfMeasureViewSet, basename='unit-of-measure')
router.register(r'external-persons', ExternalPersonViewSet, basename='external-person')
# Tokens (ruta general al final)
router.register(r'', TokenRequestViewSet, basename='token')

urlpatterns = [
    # Vistas públicas (sin autenticación)
    # IMPORTANTE: Las rutas más específicas PRIMERO
    # Ruta específica por display_number
    path('public/code/<str:display_number>/', public_token_by_code, name='public-token-by-code'),
    # Verificación rápida
    path('public/verify/<str:token_code>/', public_token_verify, name='public-token-verify'),
    # PDF público
    path('public/<str:token_code>/pdf/', public_token_pdf, name='public-token-pdf'),
    # Acepta UUID o display_number (TK-2026-000001) - MÁS GENERAL, AL FINAL
    path('public/<str:token_code>/', public_token_detail, name='public-token-detail'),

    # Rutas del ViewSet
    path('', include(router.urls)),
]
