import datetime

from django.core.validators import RegexValidator

from apps.maintenance.models import DriverModel, ProductModel, TransporterModel, TrailerModel, LocationModel, \
    OperatorModel, OutputTypeModel, DistributorCenter
from .typeDetailOutput import TypeDetailOutputModel
from apps.user.models import UserModel

from django.db import models
from utils.BaseModel import BaseModel

regex_number = '^[0-9]+$'


# Modelo para los trackers

class TrackerModel(BaseModel):
    trailer = models.ForeignKey(
        TrailerModel,
        on_delete=models.SET_NULL,
        verbose_name="Trailer",
        related_name='tracker_trailer',
        null=True
    )

    transporter = models.ForeignKey(
        TransporterModel,
        on_delete=models.SET_NULL,
        verbose_name="Transportista",
        related_name='tracker_transporter',
        null=True
    )

    # Usuario que creo el tracker
    user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        verbose_name="Usuario",
        related_name='tracker_user',
        null=True,
        blank=False
    )

    # Numero de placa del trailer
    plate_number = models.CharField(
        "Número de placa",
        max_length=50,
        null=True,
        blank=True)

    # numero de documento de entrada
    input_document_number = models.CharField(
        "Número de documento de entrada",
        max_length=50,
        unique=True,
        null=True,
        blank=False,
        validators=[RegexValidator(regex=regex_number, message='El numero de documento de entrada debe ser un numero')],
        error_messages={
            'unique': 'El numero de documento de entrada ya existe, debe ser unico'
        }
    )

    # numero de documento de salida
    output_document_number = models.CharField(
        "Número de documento de salida",
        max_length=50,
        unique=True,
        null=True,
        blank=False,
        validators=[RegexValidator(regex=regex_number, message='El numero de documento de salida debe ser un numero')],
        error_messages={
            'unique': 'El numero de documento de salida ya existe, debe ser unico'
        }
    )

    # Numero de traslado
    transfer_number = models.CharField(
        "Número de traslado",
        max_length=50,
        unique=True,
        null=True,
        blank=False,
        validators=[RegexValidator(regex=regex_number, message='El numero de traslado debe ser un numero')],
        error_messages={
            'unique': 'El numero de traslado 5001 ya existe, debe ser unico'
        }
    )

    # contabilizado
    accounted = models.CharField(
        "Contabilizado",
        max_length=50,
        null=True,
        validators=[RegexValidator(regex=regex_number, message='El numero de traslado debe ser un numero')],
        blank=True)

    # centro de distribucion
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de distribución",
        related_name='tracker_distributor_center',
        null=True,
        blank=True
    )

    # Localidad de origen
    origin_location = models.ForeignKey(
        LocationModel,
        on_delete=models.SET_NULL,
        verbose_name="Localidad de origen",
        related_name='tracker_origin_location',
        null=True,
        blank=True
    )

    # Localidad de destino
    destination_location = models.ForeignKey(
        LocationModel,
        on_delete=models.SET_NULL,
        verbose_name="Localidad de destino",
        related_name='tracker_destination_location',
        null=True,
        blank=True
    )

    # Operador #1

    operator_1 = models.ForeignKey(
        OperatorModel,
        on_delete=models.SET_NULL,
        verbose_name="Operador 1",
        related_name='tracker_operator_1',
        null=True,
        blank=True
    )

    # Operador #2
    operator_2 = models.ForeignKey(
        OperatorModel,
        on_delete=models.SET_NULL,
        verbose_name="Operador 2",
        related_name='tracker_operator_2',
        null=True,
        blank=True
    )

    # Conductor
    driver = models.ForeignKey(
        DriverModel,
        on_delete=models.SET_NULL,
        verbose_name="Conductor",
        related_name='tracker_driver',
        null=True,
        blank=True
    )

    # Tipo de salida
    output_type = models.ForeignKey(
        OutputTypeModel,
        on_delete=models.SET_NULL,
        verbose_name="Tipo de salida",
        related_name='tracker_output_type',
        null=True,
        blank=True
    )

    # Registro de entrada
    input_date = models.DateTimeField(
        "Fecha de entrada",
        null=True,
        blank=True)

    # Registro de salida
    output_date = models.DateTimeField(
        "Fecha de salida",
        null=True,
        blank=True)

    # Tiempo invertido
    time_invested = models.IntegerField(
        "Tiempo invertido",
        null=True,
        blank=True)

    STATUS_CHOICES = (
        ('PENDING', 'PENDING'),
        ('COMPLETE', 'COMPLETE'),
        ('EDITED', 'EDITED')
    )

    # Estados del tracker ['PENDING', 'COMPLETE']
    status = models.CharField(
        "Estado",
        max_length=50,
        choices=STATUS_CHOICES,
        default='EDITED')

    TYPES_CHOICES = (
        ('LOCAL', 'LOCAL'),
        ('IMPORT', 'IMPORT'),
    )

    # Tipo de tracker ['LOCAL', 'IMPORT']
    type = models.CharField(
        "Tipo",
        max_length=50,
        choices=TYPES_CHOICES,
        default='LOCAL')

    # Fehca de completado
    completed_date = models.DateTimeField(
        "Fecha de completado",
        null=True,
        blank=True)

    # numero de contenedor
    container_number = models.CharField(
        "Número de contenedor",
        max_length=50,
        null=True,
        blank=True)

    # Factura
    invoice_number = models.CharField(
        "Número de factura",
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        error_messages={
            'unique': 'El numero de factura ya existe, debe ser unico'
        }
    )

    class Meta:
        db_table = "tracker"
        verbose_name = "Tracker"
        verbose_name_plural = "Trackers"

    def __str__(self):
        # id del tracker
        return str(self.id) + " - " + str(self.input_document_number)

    # Solo se puede actualizar o eliminar si el estado es PENDING
    def complete(self):
        self.status = 'COMPLETE'
        self.save()

    def save (self, *args, **kwargs):
        if self.input_date and self.output_date:
            self.time_invested = (self.output_date - self.input_date).total_seconds()
        super(TrackerModel, self).save(*args, **kwargs)


# Modelo para los detalles de los trackers

class TrackerDetailModel(BaseModel):
    # Tracker
    tracker = models.ForeignKey(
        TrackerModel,
        on_delete=models.SET_NULL,
        verbose_name="Tracker",
        related_name='tracker_detail',
        null=True,
        blank=True
    )

    # Producto
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.SET_NULL,
        verbose_name="Producto",
        related_name='tracker_detail_product',
        null=True,
        blank=True
    )

    # Cantidad
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    class Meta:
        unique_together = ('tracker', 'product')
        db_table = "tracker_detail"
        verbose_name = "Detalle de tracker"
        verbose_name_plural = "Detalles de tracker"

    def __str__(self):
        return self.product.name + " - " + str(self.tracker)


# Modelo para los detalles de productos de los trackers

class TrackerDetailProductModel(BaseModel):
    # Tracker detalle
    tracker_detail = models.ForeignKey(
        TrackerDetailModel,
        on_delete=models.SET_NULL,
        verbose_name="Tracker detalle",
        related_name='tracker_product_detail',
        null=True,
        blank=True
    )

    # Fecha de vencimiento
    expiration_date = models.DateField(
        "Fecha de vencimiento",
        null=True,
        blank=True)

    # Cantidad
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    class Meta:
        db_table = "tracker_detail_product"
        verbose_name = "Detalle de producto de tracker"
        verbose_name_plural = "Detalles de producto de tracker"


# Detalle de salida de tracker
class TrackerDetailOutputModel(BaseModel):
    # Tracker
    tracker = models.ForeignKey(
        TrackerModel,
        on_delete=models.SET_NULL,
        verbose_name="Tracker",
        related_name='tracker_detail_output',
        null=True,
        blank=True
    )

    # Tipo de producto
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.SET_NULL,
        verbose_name="Producto",
        related_name='tracker_detail_output_product',
        null=True,
        blank=True
    )

    # Cantidad
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    # Fecha de vencimiento
    expiration_date = models.DateField(
        "Fecha de vencimiento",
        default= datetime.date.today,
    )

    class Meta:
        db_table = "tracker_detail_output"
        verbose_name = "Detalle de salida de tracker"
        verbose_name_plural = "Detalles de salida de tracker"
        unique_together = ('tracker', 'product')
