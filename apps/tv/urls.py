from rest_framework.routers import DefaultRouter

from .views import TvSessionViewSet

router = DefaultRouter()
router.register(r'tv/sessions', TvSessionViewSet, basename='tv-session')
