from rest_framework import routers

# local
from .views import CentroDistribucionViewSet, RouteModelViewSet, LocationModelViewSet, OperatorModelViewSet, TransporterModelViewSet, TrailerModelViewSet, DriverModelViewSet, ProductModelViewSet
# Routers
router = routers.DefaultRouter()
router.register(r'distribution-center', CentroDistribucionViewSet)
router.register(r'route', RouteModelViewSet)
router.register(r'location', LocationModelViewSet)
router.register(r'operator', OperatorModelViewSet)
router.register(r'transporter', TransporterModelViewSet)
router.register(r'trailer', TrailerModelViewSet)
router.register(r'driver', DriverModelViewSet)
router.register(r'product', ProductModelViewSet)
