from django.db import models
from utils.BaseModel import BaseModel
from .order import OrderModel

# Modelo de salida de orden 1:1
class OutOrderModel(BaseModel):
    # orden de salida
    order = models.OneToOneField(
        OrderModel,
        on_delete=models.CASCADE,
        verbose_name="Orden",
        related_name="out_order")

    # flota: propiedad/tercera
    fleet_choices = (
        ('PROPIEDAD', 'Propiedad'),
        ('TERCERA', 'Tercera'),
    )
    fleet = models.CharField(
        "Flota",
        max_length=50,
        choices=fleet_choices,
        default='TERCERA')

    # Tipo salida: t1, t2
    type_choices = (
        ('T1', 'T1'),
        ('T2', 'T2'),
    )
    type = models.CharField(
        "Tipo",
        max_length=50,
        choices=type_choices,
        default='T1')

    # numero documento
    document_number = models.CharField(
        "Numero de documento",
        max_length=50,
        )
    # Documento adjunto
    document = models.BinaryField(
        "Documento",
        null=True,
        blank=True)

    # vehiculo
    vehicle = models.CharField(
        "Vehiculo",
        max_length=50
        )

    document_name = models.CharField(
        "Nombre documento",
        max_length=50,
        null=True,
        blank=True)
    class Meta:
        db_table = "out_order"
        verbose_name = "Orden de salida"
        verbose_name_plural = "Ordenes de salida"

    def __str__(self):
        return self.order.distributor_center.name + " - " + self.order.user.first_name + " " + self.order.user.last_name + ' id=' + str(self.id)