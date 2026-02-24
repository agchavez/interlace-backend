from django.db import models
from utils.BaseModel import BaseModel


class ExitPassDetail(BaseModel):
    """Detalle del pase de salida de materiales/productos"""

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='exit_pass_detail',
        verbose_name='Token'
    )

    # Soporte para personas externas (proveedores)
    is_external = models.BooleanField(
        default=False,
        verbose_name='Es persona externa',
        help_text='Indica si el pase es para un proveedor/persona externa'
    )
    external_person = models.ForeignKey(
        'tokens.ExternalPerson',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='exit_passes',
        verbose_name='Persona externa'
    )

    destination = models.CharField(
        max_length=255,
        verbose_name='Destino'
    )
    purpose = models.TextField(
        verbose_name='Propósito/Motivo'
    )
    vehicle_plate = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Placa del Vehículo'
    )
    driver_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre del Conductor'
    )
    expected_return_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Esperada de Retorno'
    )

    class Meta:
        db_table = 'app_token_exit_pass_detail'
        verbose_name = 'Detalle de Pase de Salida'
        verbose_name_plural = 'Detalles de Pases de Salida'

    def __str__(self):
        return f"Pase de salida - {self.token.display_number}"

    @property
    def total_value(self):
        """Calcula el valor total de todos los items"""
        return sum(item.total_value for item in self.items.all())

    @property
    def requires_level_3_approval(self):
        """Determina si requiere aprobación nivel 3 basado en el valor total"""
        return self.total_value > 20000

    def determine_approval_levels(self):
        """
        Determina los niveles de aprobación según el valor total:
        - < 5000: L1, L2
        - 5000 - 20000: L1, L2
        - > 20000: L1, L2, L3
        """
        total = self.total_value
        if total > 20000:
            return (True, True, True)  # L1, L2, L3
        return (True, True, False)  # L1, L2


class ExitPassItem(BaseModel):
    """Item individual del pase de salida"""

    exit_pass = models.ForeignKey(
        ExitPassDetail,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pase de Salida'
    )
    material = models.ForeignKey(
        'tokens.Material',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='exit_pass_items',
        verbose_name='Material'
    )
    product = models.ForeignKey(
        'maintenance.ProductModel',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='exit_pass_items',
        verbose_name='Producto'
    )
    custom_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Descripción Personalizada'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Cantidad'
    )
    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso (kg)',
        help_text='Peso en kilogramos del material'
    )
    unit_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Unitario'
    )
    total_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total'
    )
    requires_return = models.BooleanField(
        default=False,
        verbose_name='Requiere Devolución'
    )
    return_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Devolución'
    )
    returned = models.BooleanField(
        default=False,
        verbose_name='Devuelto'
    )
    returned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Devolución Real'
    )
    returned_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Cantidad Devuelta'
    )
    return_notes = models.TextField(
        blank=True,
        verbose_name='Notas de Devolución'
    )

    class Meta:
        db_table = 'app_token_exit_pass_item'
        verbose_name = 'Item de Pase de Salida'
        verbose_name_plural = 'Items de Pase de Salida'

    def __str__(self):
        description = self.custom_description or (
            self.material.name if self.material else
            self.product.name if self.product else 'Item'
        )
        return f"{description} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Calcular valor total automáticamente
        self.total_value = self.quantity * self.unit_value
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Verifica si el item está vencido para devolución"""
        if not self.requires_return or not self.return_date or self.returned:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.return_date
