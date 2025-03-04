# SECCION: IMPORTACION DE RECURSOS DE DJANGO 
from django.db import models

# SECCION: IMPORTACION DE RECURSOS LOCALES 
from apps.user.models.user import UserModel

class LogActionModel(models.Model):
    class Meta:
        verbose_name = 'Log Action'
        verbose_name_plural = 'Log Actions'
        db_table = 'app_log_action'

    class ActionTypes(models.TextChoices):
        CREATE = 'CREAR'
        UPDATE = 'ACTUALIZAR'
        DELETE = 'ELIMINAR'
        VIEW = 'VER'
        PRINT = 'IMPRIMIR'
        DOWNLOAD = 'DESCARGAR'
        LOGIN = 'INICIO_SESION',
        EMAIL = 'ENVIO_CORREO'

    class Modules(models.TextChoices):
        T1 = 'T1'
        T2 = 'T2'
        IMPORTED = 'IMPORTED'
        USER = 'USER'


    name = models.CharField(
        max_length=100, 
        unique=True, 
        error_messages={
            'unique': 'El nombre de la acción ya existe'
        }
    )
    action = models.CharField(
        max_length=18,
        choices=ActionTypes.choices,
        default=ActionTypes.CREATE
    )
    description = models.CharField(
        max_length=100
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    module = models.CharField(
        max_length=100,
        choices=Modules.choices
    )
    def __str__(self):
        return self.name


class LogControlModel(models.Model):
    class Meta:
        verbose_name = 'Log Control'
        verbose_name_plural = 'Log Controls'
        db_table = 'app_log_control'

    user = models.ForeignKey(
        UserModel, 
        on_delete=models.CASCADE, 
        blank = True,
        null=True,
        related_name='user_logs'
    )
    action = models.ForeignKey(
        LogActionModel, 
        on_delete=models.CASCADE, 
        related_name='action_logs'
    )
    description = models.TextField(
        blank = True,
        null=True
    )
    data = models.JSONField(
        blank=True,
        null=True
    )
    id_register = models.IntegerField(
        blank = True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.action.name