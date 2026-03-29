from rest_framework import routers

# local
from .views import (
        CentroDistribucionViewSet,
        RouteModelViewSet,
        LocationModelViewSet,
        OperatorModelViewSet,
        TransporterModelViewSet,
        TrailerModelViewSet,
        DriverModelViewSet,
        ProductModelViewSet,
        OutputTypeModelViewSet,
        LotModelViewSet,
        PeriodViewSet,
        CountryViewSet)
from .views.centro_distribucion import DCShiftViewSet

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
router.register(r'output-type', OutputTypeModelViewSet)
router.register(r'period', PeriodViewSet)
router.register(r'lot', LotModelViewSet)
router.register(r'country', CountryViewSet)
router.register(r'dc-shift', DCShiftViewSet)
