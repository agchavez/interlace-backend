from django.db import models

# local
from utils.BaseModel import BaseModel
from .distributor_center import DistributorCenter

# Modelo para el mantenimiento de los operadores por centro de distribución
class OperatorModel(BaseModel):
    first_name = models.CharField(
        "Nombre",
        max_length=50)
    last_name = models.CharField(
        "Apellido",
        max_length=50)
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        null=True,
        blank=True)


    def __str__(self):
        return self.first_name + " " + self.last_name + " - " + self.distributor_center.name

    class Meta:
        db_table = "operator"
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"