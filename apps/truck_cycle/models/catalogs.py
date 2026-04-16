"""
Modelos de catálogos para el ciclo del camión
"""
from django.db import models
from apps.maintenance.models.distributor_center import DistributorCenter


class TruckModel(models.Model):
    """Catálogo de camiones"""

    PALLET_TYPE_CHOICES = [
        ('STANDARD', 'Estándar'),
        ('HALF', 'Media'),
    ]

    code = models.CharField(
        "Código",
        max_length=20,
    )
    plate = models.CharField(
        "Placa",
        max_length=20,
    )
    pallet_type = models.CharField(
        "Tipo de Tarima",
        max_length=10,
        choices=PALLET_TYPE_CHOICES,
    )
    pallet_spaces = models.PositiveIntegerField(
        "Espacios de Tarima",
    )
    is_active = models.BooleanField(
        "Activo",
        default=True,
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de Distribución",
        related_name="trucks",
    )

    class Meta:
        db_table = "truck_cycle_truck"
        verbose_name = "Camión"
        verbose_name_plural = "Camiones"
        unique_together = ['code', 'distributor_center']

    def __str__(self):
        return f"{self.code} - {self.plate}"


class ProductCatalogModel(models.Model):
    """Catálogo de productos"""

    sku_code = models.CharField(
        "Código SKU",
        max_length=20,
    )
    description = models.CharField(
        "Descripción",
        max_length=200,
    )
    division = models.CharField(
        "División",
        max_length=100,
        blank=True,
    )
    brand = models.CharField(
        "Marca",
        max_length=100,
        blank=True,
    )
    boxes_per_pallet = models.PositiveIntegerField(
        "Cajas por Tarima",
        default=1,
    )
    is_active = models.BooleanField(
        "Activo",
        default=True,
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de Distribución",
        related_name="product_catalogs",
    )

    class Meta:
        db_table = "truck_cycle_product_catalog"
        verbose_name = "Catálogo de Producto"
        verbose_name_plural = "Catálogo de Productos"
        unique_together = ['sku_code', 'distributor_center']

    def __str__(self):
        return f"{self.sku_code} - {self.description}"


class BayModel(models.Model):
    """Catálogo de andenes"""

    code = models.CharField(
        "Código",
        max_length=10,
    )
    name = models.CharField(
        "Nombre",
        max_length=50,
    )
    is_active = models.BooleanField(
        "Activo",
        default=True,
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de Distribución",
        related_name="bays",
    )

    class Meta:
        db_table = "truck_cycle_bay"
        verbose_name = "Andén"
        verbose_name_plural = "Andenes"

    def __str__(self):
        return f"{self.code} - {self.name}"


class KPITargetModel(models.Model):
    """Metas de KPIs"""

    KPI_TYPE_CHOICES = [
        ('BOXES_PER_HOUR', 'Cajas por Hora'),
        ('COUNT_ACCURACY', 'Precisión de Conteo'),
        ('PICKING_ERROR_RATE', 'Tasa de Error de Picking'),
        ('LOADING_TIME', 'Tiempo de Carga'),
        ('DISPATCH_TIME', 'Tiempo de Despacho'),
    ]

    kpi_type = models.CharField(
        "Tipo de KPI",
        max_length=30,
        choices=KPI_TYPE_CHOICES,
    )
    target_value = models.DecimalField(
        "Valor Meta",
        max_digits=10,
        decimal_places=2,
    )
    unit = models.CharField(
        "Unidad",
        max_length=20,
    )
    warning_threshold = models.DecimalField(
        "Umbral de Alerta",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    effective_from = models.DateField(
        "Vigente Desde",
    )
    effective_to = models.DateField(
        "Vigente Hasta",
        null=True,
        blank=True,
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de Distribución",
        related_name="kpi_targets",
    )

    class Meta:
        db_table = "truck_cycle_kpi_target"
        verbose_name = "Meta de KPI"
        verbose_name_plural = "Metas de KPI"

    def __str__(self):
        return f"{self.get_kpi_type_display()} - {self.target_value} {self.unit}"
