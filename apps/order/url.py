from rest_framework import routers

# local
from .views import OrderDetailViewSet, OrderHistoryViewSet, OrderViewSet
# Routers
router = routers.DefaultRouter()

router.register(r'order', OrderViewSet, basename='order')
router.register(r'order-detail', OrderDetailViewSet, basename='order-detail')
router.register(r'order-history', OrderHistoryViewSet, basename='order-history')