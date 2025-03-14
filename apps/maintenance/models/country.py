
from django.db import models
from utils.BaseModel import BaseModel

# Modelo para el mantenimiento de paises
class CountryModel(BaseModel):
    class Meta:
        db_table = "country"
        verbose_name = "Pais"
        verbose_name_plural = "Paises"
        ordering = ['-created_at']

    # Nombre del pais
    name = models.CharField(max_length=75, null=False)

    # Codigo del pais
    code = models.CharField(max_length=5, null=False)

    # Bandera del pais
    flag = models.CharField(max_length=150, null=True)

    def __str__(self):
        return self.name