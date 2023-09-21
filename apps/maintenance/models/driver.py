from django.db import models

# local
from utils.BaseModel import BaseModel

class DriverModel(BaseModel):
    first_name = models.CharField(
        "Nombre",
        max_length=50)
    last_name = models.CharField(
        "Apellido",
        max_length=50)
    code = models.CharField(
        "Código",
        max_length=50,
        unique=True)
    sap_code = models.CharField(
        "Código SAP",
        max_length=10,
        unique=True)


    def __str__(self):
        return self.first_name + " " + self.last_name


    def save(self, *args, **kwargs):
        self.first_name = self.first_name.upper()
        self.last_name = self.last_name.upper()
        return super(DriverModel, self).save(*args, **kwargs)

    class Meta:
        db_table = "driver"
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"