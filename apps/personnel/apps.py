from django.apps import AppConfig


class PersonnelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.personnel'
    verbose_name = 'Gestión de Personal'

    def ready(self):
        import apps.personnel.signals
