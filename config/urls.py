from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path, include

from apps.user.url import router as user_router
from apps.authentication.url import router as auth_router
from apps.maintenance.url import router as maintenance_router
from apps.tracker.url import router as tracker_router
from apps.report.url import router as report_router
from apps.order.url import router as order_router
from apps.inventory.url import router as inventory_router

router = DefaultRouter()
router.registry.extend(user_router.registry)
router.registry.extend(auth_router.registry)
router.registry.extend(maintenance_router.registry)
router.registry.extend(tracker_router.registry)
router.registry.extend(report_router.registry)
router.registry.extend(order_router.registry)
router.registry.extend(inventory_router.registry)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
