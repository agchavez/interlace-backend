from django.db import models
from utils.BaseModel import BaseModel


class UnitOfMeasure(BaseModel):
    """Unidad de medida para materiales"""

    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Código'
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Nombre'
    )
    abbreviation = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Abreviatura'
    )

    class Meta:
        db_table = 'app_token_unit_of_measure'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class OvertimeTypeModel(BaseModel):
    """Tipos de horas extra configurables"""

    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Categoría'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    default_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.5,
        verbose_name='Multiplicador por Defecto'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    class Meta:
        db_table = 'app_token_overtime_type'
        verbose_name = 'Tipo de Hora Extra'
        verbose_name_plural = 'Tipos de Horas Extra'
        ordering = ['name']

    def __str__(self):
        return self.name


class OvertimeReasonModel(BaseModel):
    """Motivos de horas extra configurables"""

    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Categoría'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    class Meta:
        db_table = 'app_token_overtime_reason'
        verbose_name = 'Motivo de Hora Extra'
        verbose_name_plural = 'Motivos de Horas Extra'
        ordering = ['name']

    def __str__(self):
        return self.name


class Material(BaseModel):
    """Catálogo de materiales para pases de salida"""

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='materials',
        verbose_name='Unidad de Medida'
    )
    unit_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Unitario'
    )
    requires_return = models.BooleanField(
        default=False,
        verbose_name='Requiere Devolución'
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Categoría'
    )

    class Meta:
        db_table = 'app_token_material'
        verbose_name = 'Material'
        verbose_name_plural = 'Materiales'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
