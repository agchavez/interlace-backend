# django
import datetime

from django.db import models
from django.utils import timezone

# local
from utils.BaseModel import BaseModel
from apps.maintenance.models import DriverModel, ProductModel, TransporterModel, TrailerModel, LocationModel, \
    OperatorModel, OutputTypeModel, DistributorCenter, LotModel
from apps.tracker.models import TrackerDetailProductModel
from apps.user.models import UserModel

# Modelo para encabezado de salida de productos t2
class OutputT2Model(BaseModel):
    # usuario que carga la salida
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        related_name="user_output_t2")

    # usuario que autoriza la salida
    user_authorizer = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Usuario autorizador",
        related_name="user_authorizer_output_t2",
        null=True,
        blank=True)

    # usuario que recibe la salida
    user_applied = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Usuario receptor",
        related_name="user_receiver_output_t2",
        null=True,
        blank=True)

    # usuario check
    user_check = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Usuario check",
        related_name="user_check_output_t2",
        null=True,
        blank=True)

    # Estados de la salida
    choices_status = [
        ('CREATED', 'CREATED'),
        ('CHECKED', 'CHECKED'),
        ('REJECTED', 'REJECTED'),
        ('AUTHORIZED', 'AUTHORIZED'),
        ('APPLIED', 'APPLIED'),
    ]

    # Estado de la salida
    status = models.CharField(
        "Estado",
        max_length=10,
        choices=choices_status,
        default='CREATED')

    # Centro de distribución
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de distribución",
        related_name="distributor_center_output_t2")

    # Observaciones
    observations = models.CharField(
        "Observaciones",
        max_length=200,
        null=True,
        blank=True)

    # ultima actualizacion
    last_update = models.DateTimeField(
        "Ultima actualización",
        auto_now=True)

    # json de la simulacion
    simulation = models.JSONField(
        "simulación",
        null=True,
        blank=True)

    # fecha de preventa
    pre_sale_date = models.DateField(
        "Fecha de preventa",
        default= datetime.date.today
        )


    class Meta:
        db_table = "output_t2"
        verbose_name = "Salida T2"
        verbose_name_plural = "Salidas T2"


# Modelo para el detalle de salida de productos t2

class OutputDetailT2Model(BaseModel):
    # salida
    output = models.ForeignKey(
        OutputT2Model,
        on_delete=models.CASCADE,
        verbose_name="Salida",
        related_name="output_detail_t2")

    # producto
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        verbose_name="Producto",
        related_name="product_output_detail_t2")

    # cantidad
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    # observaciones mootivo del rechazo
    observations = models.CharField(
        "Observaciones",
        max_length=200,
        null=True,
        blank=True)

    # Estados de la salida
    choices_status = [
        ('CREATED', 'CREATED'),
        ('CHECKED', 'CHECKED'),
        ('REJECTED', 'REJECTED'),
        ('AUTHORIZED', 'AUTHORIZED'),
        ('APPLIED', 'APPLIED'),
    ]

    # Estado de la salida
    status = models.CharField(
        "Estado",
        max_length=10,
        choices=choices_status,
        default='CREATED')

    class Meta:
        db_table = "output_detail_t2"
        verbose_name = "Detalle de salida T2"
        verbose_name_plural = "Detalles de salida T2"

    def __str__(self):
        return str(self.output.id) + ' - ' +  self.product.name + ' - ' + str(self.quantity) + ' - ' + self.status


# Modelo de los trackers de salida de productos t2
class TrackerOutputT2Model(BaseModel):

    # salida
    output_detail = models.ForeignKey(
        OutputDetailT2Model,
        on_delete=models.CASCADE,
        verbose_name="Salida",
        null=True,
        related_name="output_detail_tracker_t2")

    # tracker
    tracker_detail = models.ForeignKey(
        TrackerDetailProductModel,
        on_delete=models.SET_NULL,
        verbose_name="Tracker",
        null=True,
        related_name="tracker_detail_output_t2")

    lote = models.ForeignKey(
        LotModel,
        on_delete=models.SET_NULL,
        verbose_name="Lote",
        null=True,
        blank=True,
        related_name="lote_output_t2")


    # cantidad
    quantity = models.IntegerField(
    "Cantidad",
    default=0)

    class Meta:
        db_table = "tracker_output_t2"
        verbose_name = "Tracker de salida T2"
        verbose_name_plural = "Trackers de salida T2"
