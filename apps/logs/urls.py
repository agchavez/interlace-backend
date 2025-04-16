from rest_framework import routers

from .views.logs import LogControlView, LogActionView

router = routers.DefaultRouter()
router.register(r'logs', LogControlView)
router.register(r'logs_action', LogActionView)

