from django.db import models

# local
from utils.BaseModel import BaseModel
from .distributor_center import DistributorCenter

# Modelo para el mantenimiento de los operadores por centro de distribución
class OperatorModel(BaseModel):
    first_name = models.CharField(
        "Nombre",
        max_length=60)

    last_name = models.CharField(
        "Apellido",
        max_length=60)

    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        null=True,
        blank=True)


    def __str__(self):
        return self.first_name + " - " + self.distributor_center.name


    def save(self, *args, **kwargs):
        self.first_name = self.first_name.upper()
        return super(OperatorModel, self).save(*args, **kwargs)

    class Meta:
        db_table = "operator"
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"