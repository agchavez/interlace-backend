from django.apps import AppConfig


class TruckCycleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.truck_cycle'
    verbose_name = 'Ciclo del Camión'

    def ready(self):
        import apps.truck_cycle.signals  # noqa: F401
