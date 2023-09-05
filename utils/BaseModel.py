
# Importaciones
from django.db import models
# Modelo base con los campos createdAt, updatedAt por hora y por fecha
class BaseModel(models.Model):
    created_at_date = models.DateField(
        "Fecha de Creación",
        auto_now_add=True,
        null=True)
    created_at_time = models.TimeField(
        "Hora de Creación",
        auto_now_add=True,
        null=True)


    class Meta:
        abstract = True
        verbose_name = "Modelo Base"
        verbose_name_plural = "Modelos Base"
        ordering = ['created_at', 'updated_at']


