from rest_framework import routers

# local
from .views import TrackerModelViewSet, TrackerDetailModelViewSet, TrackerDetailProductModelViewSet, TrackerDetailOutputView

# Routers
router = routers.DefaultRouter()
router.register(r'tracker', TrackerModelViewSet, basename='tracker')
router.register(r'tracker-detail', TrackerDetailModelViewSet, basename='tracker-detail')
router.register(r'tracker-detail-product', TrackerDetailProductModelViewSet, basename='tracker-detail-product')
router.register(r'tracker-detail-output', TrackerDetailOutputView, basename='tracker-detail-output')
