from rest_framework.routers import DefaultRouter
from django.urls import path, include

# Views
from apps.authentication.views import AuthView

# Routers
router = DefaultRouter()
router.register(r'auth', AuthView, basename='auth')  # Aquí definimos 'auth' como el nombre base personalizado
