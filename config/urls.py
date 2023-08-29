from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path, include

from apps.user.url import router as user_router
from apps.authentication.url import router as auth_router
router = DefaultRouter()
router.registry.extend(user_router.registry)
router.registry.extend(auth_router.registry)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
