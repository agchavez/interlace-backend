
from django.db import models
# Modelo para el mantenimiento de los centros de distribución
class CentroDistribucion(models.Model):
    nombre = models.CharField(max_length=50)
    direccion = models.CharField(max_length=50, null=True)
    telefono = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "centro_distribucion"
        verbose_name = "Centro de Distribución"
        verbose_name_plural = "Centros de Distribución"