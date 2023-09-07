from django.db import models

# local
from utils.BaseModel import BaseModel

# Modelo para los tipos de salida de producto
class TypeDetailOutputModel(BaseModel):
    name = models.CharField(
        "Nombre",
        max_length=50)

    detail_required = models.BooleanField(
        "Requiere detalles",
        default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "type_detail_output"
        verbose_name = "Tipo de salida de producto"
        verbose_name_plural = "Tipos de salida de producto"