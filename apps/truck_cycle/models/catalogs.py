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
    primary_driver = models.ForeignKey(
        'personnel.PersonnelProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_trucks',
        verbose_name="Chofer asignado",
        help_text="Chofer vendedor asignado por defecto a este camión.",
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
    row = models.PositiveIntegerField(
        "Fila",
        default=0,
        help_text="Fila en el grid visual del estacionamiento (0-indexed).",
    )
    column = models.PositiveIntegerField(
        "Columna",
        default=0,
        help_text="Columna en el grid visual del estacionamiento (0-indexed).",
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
        ordering = ['row', 'column', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class KPITargetModel(models.Model):
    """Metas de KPIs por centro de distribución.

    Soporta dos modalidades coexistentes:
    - Legacy: `kpi_type` con enum fijo (5 valores).
    - Nuevo: `metric_type` FK a PerformanceMetricType + `direction` para
      semaforizar samples de truck_cycle.
    El sistema de bandas (verde/amarillo/rojo) usa `target_value` (meta),
    `warning_threshold` (disparador) y `direction`.
    """

    KPI_TYPE_CHOICES = [
        ('BOXES_PER_HOUR', 'Cajas por Hora'),
        ('COUNT_ACCURACY', 'Precisión de Conteo'),
        ('PICKING_ERROR_RATE', 'Tasa de Error de Picking'),
        ('LOADING_TIME', 'Tiempo de Carga'),
        ('DISPATCH_TIME', 'Tiempo de Despacho'),
    ]

    DIRECTION_HIGHER_IS_BETTER = 'HIGHER_IS_BETTER'
    DIRECTION_LOWER_IS_BETTER = 'LOWER_IS_BETTER'
    DIRECTION_CHOICES = [
        (DIRECTION_HIGHER_IS_BETTER, 'Mayor es mejor'),
        (DIRECTION_LOWER_IS_BETTER, 'Menor es mejor'),
    ]

    kpi_type = models.CharField(
        "Tipo de KPI (legacy)",
        max_length=30,
        choices=KPI_TYPE_CHOICES,
        null=True,
        blank=True,
    )
    metric_type = models.ForeignKey(
        'personnel.PerformanceMetricType',
        on_delete=models.CASCADE,
        verbose_name="Tipo de métrica",
        related_name="kpi_targets",
        null=True,
        blank=True,
        help_text="Vincula la meta a un PerformanceMetricType (nueva modalidad).",
    )
    direction = models.CharField(
        "Dirección",
        max_length=20,
        choices=DIRECTION_CHOICES,
        default=DIRECTION_HIGHER_IS_BETTER,
    )
    target_value = models.DecimalField(
        "Meta",
        max_digits=10,
        decimal_places=2,
    )
    unit = models.CharField(
        "Unidad",
        max_length=20,
        blank=True,
    )
    warning_threshold = models.DecimalField(
        "Disparador",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor a partir del cual se marca en amarillo (antes del rojo).",
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
        indexes = [
            models.Index(fields=['metric_type', 'distributor_center', '-effective_from']),
        ]

    def __str__(self):
        label = self.metric_type.name if self.metric_type else self.get_kpi_type_display()
        return f"{label} - {self.target_value} {self.unit}".strip()
