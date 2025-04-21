from rest_framework import routers

# local
from .views import TrackerModelViewSet, TrackerDetailModelViewSet, TrackerDetailProductModelViewSet, TrackerDetailOutputView, OutputDetailT2View, OutputT2View, TrackerOutputT2View

# Routers
router = routers.DefaultRouter()
router.register(r'tracker', TrackerModelViewSet, basename='tracker')
router.register(r'tracker-detail', TrackerDetailModelViewSet, basename='tracker-detail')
router.register(r'tracker-detail-product', TrackerDetailProductModelViewSet, basename='tracker-detail-product')
router.register(r'tracker-detail-output', TrackerDetailOutputView, basename='tracker-detail-output')
router.register(r'output-t2', OutputT2View, basename='output-t2')
router.register(r'output-detail-t2', OutputDetailT2View, basename='output-detail-t2')
router.register(r'tracker-output-t2', TrackerOutputT2View, basename='tracker-output-t2')