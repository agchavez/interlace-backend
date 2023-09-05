from rest_framework import routers

# local
from .views import CentroDistribucionViewSet, RouteModelViewSet, LocationModelViewSet, OperatorModelViewSet, TransporterModelViewSet, TrailerModelViewSet
# Routers
router = routers.DefaultRouter()
router.register(r'distribution-center', CentroDistribucionViewSet)
router.register(r'route', RouteModelViewSet)
router.register(r'location', LocationModelViewSet)
router.register(r'operator', OperatorModelViewSet)
router.register(r'transporter', TransporterModelViewSet)
router.register(r'trailer', TrailerModelViewSet)