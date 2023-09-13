from rest_framework import routers

# local
from .views import TrackerModelViewSet, TrackerDetailModelViewSet, TrackerDetailProductModelViewSet

# Routers
router = routers.DefaultRouter()
router.register(r'tracker', TrackerModelViewSet, basename='tracker')
router.register(r'tracker-detail', TrackerDetailModelViewSet, basename='tracker-detail')
router.register(r'tracker-detail-product', TrackerDetailProductModelViewSet, basename='tracker-detail-product')
