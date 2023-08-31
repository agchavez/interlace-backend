from rest_framework import routers

# local
from .views import CentroDistribucionViewSet
# Routers
router = routers.DefaultRouter()
router.register(r'center-distribution', CentroDistribucionViewSet)