from rest_framework import routers

# local
from .views import InventoryMovementViewSet
# Routers
router = routers.DefaultRouter()

router.register(r'inventory-movement', InventoryMovementViewSet, basename='inventory-movement')
