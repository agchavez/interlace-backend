from rest_framework import routers

# local
from .views import InventoryViewSet, InventoryMovementViewSet
# Routers
router = routers.DefaultRouter()

router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'inventory-movement', InventoryMovementViewSet, basename='inventory-movement')
