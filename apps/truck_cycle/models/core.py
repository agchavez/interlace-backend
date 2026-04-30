"""
Modelos principales del ciclo del camión
"""
from django.db import models
from django.contrib.auth import get_user_model
from utils.BaseModel import BaseModel
from apps.maintenance.models.distributor_center import DistributorCenter
from .catalogs import TruckModel, ProductCatalogModel

User = get_user_model()


class PalletComplexUploadModel(BaseModel):
    """Carga masiva de pautas de complejidad"""

    STATUS_CHOICES = [
        ('PREVIEW', 'Vista Previa'),
        ('CONFIRMED', 'Confirmada'),
        ('CANCELLED', 'Cancelada'),
    ]

    file_name = models.CharField(
        "Nombre del Archivo",
        max_length=255,
    )
    file = models.FileField(
        "Archivo",
        upload_to='truck_cycle/uploads/',
    )
    upload_date = models.DateField(
        "Fecha de Carga",
        auto_now_add=True,
    )
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=STATUS_CHOICES,
        default='PREVIEW',
    )
    errors_json = models.JSONField(
        "Errores",
        default=dict,
        blank=True,
    )
    row_count = models.PositiveIntegerField(
        "Cantidad de Filas",
        default=0,
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de Distribución",
        related_name="truck_cycle_uploads",
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Cargado por",
        related_name="truck_cycle_uploads",
    )

    class Meta:
        db_table = "truck_cycle_upload"
        verbose_name = "Carga de Pautas"
        verbose_name_plural = "Cargas de Pautas"

    def __str__(self):
        return f"{self.file_name} - {self.get_status_display()}"


class PautaModel(BaseModel):
    """Pauta principal - unidad de trabajo del ciclo del camión"""

    STATUS_CHOICES = [
        ('PENDING_PICKING', 'Pendiente de Picking'),
        ('PICKING_ASSIGNED', 'Picking Asignado'),
        ('PICKING_IN_PROGRESS', 'Picking en Progreso'),
        ('PICKING_DONE', 'Picking Completado'),
        ('MOVING_TO_BAY', 'Moviéndose a Bahía'),
        ('IN_BAY', 'En Andén'),
        ('PENDING_COUNT', 'Pendiente de Conteo'),
        ('COUNTING', 'Contando'),
        ('COUNTED', 'Contado'),
        ('MOVING_TO_PARKING', 'Moviéndose a Estacionamiento'),
        ('PARKED', 'Estacionado'),
        ('PENDING_CHECKOUT', 'Pendiente de Checkout'),
        ('CHECKOUT_SECURITY', 'Checkout Seguridad'),
        ('CHECKOUT_OPS', 'Checkout Operaciones'),
        ('DISPATCHED', 'Despachado'),
        ('IN_RELOAD_QUEUE', 'En Cola de Recarga'),
        ('PENDING_RETURN', 'Pendiente de Devolución'),
        ('RETURN_PROCESSED', 'Devolución Procesada'),
        ('IN_AUDIT', 'En Auditoría'),
        ('AUDIT_COMPLETE', 'Auditoría Completa'),
        ('CLOSED', 'Cerrada'),
        ('CANCELLED', 'Cancelada'),
    ]

    transport_number = models.CharField(
        "Número de Transporte",
        max_length=20,
    )
    trip_number = models.CharField(
        "Número de Viaje",
        max_length=10,
        blank=True,
    )
    route_code = models.CharField(
        "Código de Ruta",
        max_length=20,
        blank=True,
    )
    total_boxes = models.PositiveIntegerField(
        "Total de Cajas",
        default=0,
    )
    total_skus = models.PositiveIntegerField(
        "Total de SKUs",
        default=0,
    )
    total_pallets = models.DecimalField(
        "Total de Tarimas",
        max_digits=6,
        decimal_places=1,
        default=0,
    )
    assembled_fractions = models.PositiveIntegerField(
        "Fracciones Armadas",
        default=0,
        help_text="Cantidad de tarimas parciales armadas (no llenas).",
    )
    complexity_score = models.DecimalField(
        "Puntaje de Complejidad",
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    status = models.CharField(
        "Estado",
        max_length=30,
        choices=STATUS_CHOICES,
        default='PENDING_PICKING',
    )
    operational_date = models.DateField(
        "Fecha Operativa",
    )
    is_reload = models.BooleanField(
        "Es Recarga",
        default=False,
    )
    reload_count = models.PositiveIntegerField(
        "Cantidad de Recargas",
        default=0,
    )
    reentered_at = models.DateTimeField(
        "Re-ingreso",
        null=True,
        blank=True,
        help_text="Momento en que la recarga re-ingresó al CD.",
    )
    notes = models.TextField(
        "Notas",
        blank=True,
    )
    truck = models.ForeignKey(
        TruckModel,
        on_delete=models.CASCADE,
        verbose_name="Camión",
        related_name="pautas",
    )
    upload = models.ForeignKey(
        PalletComplexUploadModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Carga",
        related_name="pautas",
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de Distribución",
        related_name="pautas",
    )
    parent_pauta = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Pauta Padre",
        related_name="reload_pautas",
    )

    class Meta:
        db_table = "truck_cycle_pauta"
        verbose_name = "Pauta"
        verbose_name_plural = "Pautas"
        ordering = ['-operational_date', '-created_at']

    def __str__(self):
        return f"Pauta {self.transport_number} - {self.get_status_display()}"


class PautaProductDetailModel(models.Model):
    """Detalle de productos por pauta"""

    material_code = models.CharField(
        "Código de Material",
        max_length=20,
    )
    product_name = models.CharField(
        "Nombre del Producto",
        max_length=200,
    )
    category = models.CharField(
        "Categoría",
        max_length=100,
        blank=True,
    )
    total_boxes = models.PositiveIntegerField(
        "Total de Cajas",
        default=0,
    )
    full_pallets = models.PositiveIntegerField(
        "Tarimas Completas",
        default=0,
    )
    fraction = models.DecimalField(
        "Fracción",
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="product_details",
    )
    product_catalog = models.ForeignKey(
        ProductCatalogModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Catálogo de Producto",
        related_name="pauta_product_details",
    )

    class Meta:
        db_table = "truck_cycle_pauta_product"
        verbose_name = "Detalle de Producto de Pauta"
        verbose_name_plural = "Detalles de Producto de Pauta"

    def __str__(self):
        return f"{self.material_code} - {self.product_name}"


class PautaDeliveryDetailModel(models.Model):
    """Detalle de entregas por pauta"""

    route_code = models.CharField(
        "Código de Ruta",
        max_length=20,
    )
    delivery_number = models.CharField(
        "Número de Entrega",
        max_length=30,
    )
    material_code = models.CharField(
        "Código de Material",
        max_length=20,
    )
    delivery_quantity = models.PositiveIntegerField(
        "Cantidad de Entrega",
        default=0,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="delivery_details",
    )

    class Meta:
        db_table = "truck_cycle_pauta_delivery"
        verbose_name = "Detalle de Entrega de Pauta"
        verbose_name_plural = "Detalles de Entrega de Pauta"

    def __str__(self):
        return f"{self.delivery_number} - {self.material_code}"
