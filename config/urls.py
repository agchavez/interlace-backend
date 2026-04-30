from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include

from apps.user.url import router as user_router, urlpatterns as user_urlpatterns
from apps.authentication.url import router as auth_router
from apps.maintenance.url import router as maintenance_router
from apps.tracker.url import router as tracker_router
from apps.report.url import router as report_router
from apps.order.url import router as order_router
from apps.inventory.url import router as inventory_router
from apps.document.url import router as document_router
from apps.imported.url import router as imported_router
from apps.personnel.url import router as personnel_router
from apps.truck_cycle.url import router as truck_cycle_router
from apps.tv.urls import router as tv_router
from apps.workstation.urls import router as workstation_router, extra_urlpatterns as workstation_extra
from config import settings

router = DefaultRouter()
router.registry.extend(user_router.registry)
router.registry.extend(auth_router.registry)
router.registry.extend(maintenance_router.registry)
router.registry.extend(tracker_router.registry)
router.registry.extend(report_router.registry)
router.registry.extend(order_router.registry)
router.registry.extend(inventory_router.registry)
router.registry.extend(document_router.registry)
router.registry.extend(imported_router.registry)
router.registry.extend(personnel_router.registry)
router.registry.extend(truck_cycle_router.registry)
router.registry.extend(tv_router.registry)
router.registry.extend(workstation_router.registry)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include(user_urlpatterns)),
    path('api/', include(workstation_extra)),
    path('api/tokens/', include('apps.tokens.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
