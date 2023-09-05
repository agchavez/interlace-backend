from django.db import models

# local
from utils.BaseModel import BaseModel

# Modelo para el mantenimiento de los trailers y de los transportistas

class TransporterModel(BaseModel):
    # nombre del transportista
    name = models.CharField(
        "Nombre",
        max_length=50)

    # codigo del transportista unique
    code = models.CharField(
        "Código",
        max_length=50,
        unique=True)

    # tractor del transportista
    tractor = models.CharField(
        "Tractor",
        max_length=50)

    # cabezal del transportista
    head = models.CharField(
        "Cabezal",
        max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "transporter"
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"


class TrailerModel(BaseModel):
    # codigo del trailer unique
    code = models.CharField(
        "Código",
        max_length=50,
        unique=True)

    # transportista del trailer
    transporter = models.ForeignKey(
        TransporterModel,
        on_delete=models.SET_NULL,
        verbose_name="Transportista",
        null=True,
        blank=True)

    def __str__(self):
        return self.code + " - " + self.transporter.name

    class Meta:
        db_table = "trailer"
        verbose_name = "Trailer"
        verbose_name_plural = "Trailers"




