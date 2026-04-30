from django.apps import AppConfig


class WorkstationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workstation'
    verbose_name = 'Estaciones de Trabajo'

    def ready(self):
        # Registrar signals que notifican a las TVs cuando cambia la config.
        from . import signals  # noqa: F401
