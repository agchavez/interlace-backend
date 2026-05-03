from rest_framework.routers import DefaultRouter

from .views import RepackEntryViewSet, RepackSessionViewSet


router = DefaultRouter()
router.register('repack-session', RepackSessionViewSet, basename='repack-session')
router.register('repack-entry', RepackEntryViewSet, basename='repack-entry')
