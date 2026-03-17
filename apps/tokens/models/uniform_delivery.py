from django.db import models
from utils.BaseModel import BaseModel


class UniformDeliveryDetail(BaseModel):
    """Detalle de entrega de uniforme"""

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='uniform_delivery_detail',
        verbose_name='Token'
    )

    # Entrega
    is_delivered = models.BooleanField(
        default=False,
        verbose_name='Entregado'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Entrega'
    )
    delivered_by = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uniforms_delivered',
        verbose_name='Entregado por'
    )

    # Fotos de evidencia
    delivery_photo_1 = models.ImageField(
        upload_to='tokens/uniforms/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto de Entrega 1'
    )
    delivery_photo_2 = models.ImageField(
        upload_to='tokens/uniforms/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto de Entrega 2'
    )

    # Firma digital
    signature_image = models.ImageField(
        upload_to='tokens/signatures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Firma Digital'
    )

    # Ubicación de entrega
    delivery_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Ubicación de Entrega'
    )

    # Notas
    delivery_notes = models.TextField(
        blank=True,
        verbose_name='Notas de Entrega'
    )

    class Meta:
        db_table = 'app_token_uniform_delivery_detail'
        verbose_name = 'Detalle de Entrega de Uniforme'
        verbose_name_plural = 'Detalles de Entrega de Uniforme'

    def __str__(self):
        return f"Entrega de uniforme - {self.token.display_number}"

    def mark_as_delivered(self, delivered_by, signature=None, photo1=None, photo2=None, notes=''):
        """Marca la entrega como completada"""
        from django.utils import timezone

        self.is_delivered = True
        self.delivered_at = timezone.now()
        self.delivered_by = delivered_by
        if signature:
            self.signature_image = signature
        if photo1:
            self.delivery_photo_1 = photo1
        if photo2:
            self.delivery_photo_2 = photo2
        if notes:
            self.delivery_notes = notes
        self.save()


class UniformItem(BaseModel):
    """Item individual de uniforme"""

    class ItemType(models.TextChoices):
        SHIRT = 'SHIRT', 'Camisa'
        PANTS = 'PANTS', 'Pantalón'
        JACKET = 'JACKET', 'Chaqueta'
        SHOES = 'SHOES', 'Zapatos'
        BOOTS = 'BOOTS', 'Botas'
        HAT = 'HAT', 'Gorra'
        HELMET = 'HELMET', 'Casco'
        VEST = 'VEST', 'Chaleco'
        GLOVES = 'GLOVES', 'Guantes'
        BELT = 'BELT', 'Cinturón'
        BADGE = 'BADGE', 'Credencial'
        OVERALL = 'OVERALL', 'Overol'
        OTHER = 'OTHER', 'Otro'

    class Size(models.TextChoices):
        XS = 'XS', 'Extra Pequeño'
        S = 'S', 'Pequeño'
        M = 'M', 'Mediano'
        L = 'L', 'Grande'
        XL = 'XL', 'Extra Grande'
        XXL = 'XXL', 'Doble Extra Grande'
        XXXL = 'XXXL', 'Triple Extra Grande'
        # Para zapatos
        SIZE_35 = '35', 'Talla 35'
        SIZE_36 = '36', 'Talla 36'
        SIZE_37 = '37', 'Talla 37'
        SIZE_38 = '38', 'Talla 38'
        SIZE_39 = '39', 'Talla 39'
        SIZE_40 = '40', 'Talla 40'
        SIZE_41 = '41', 'Talla 41'
        SIZE_42 = '42', 'Talla 42'
        SIZE_43 = '43', 'Talla 43'
        SIZE_44 = '44', 'Talla 44'
        SIZE_45 = '45', 'Talla 45'
        NA = 'NA', 'No Aplica'

    uniform_delivery = models.ForeignKey(
        UniformDeliveryDetail,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Entrega de Uniforme'
    )
    material = models.ForeignKey(
        'tokens.Material',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='uniform_items',
        verbose_name='Material'
    )
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        blank=True,
        verbose_name='Tipo de Prenda (legacy)'
    )
    custom_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descripción Personalizada'
    )
    size = models.CharField(
        max_length=10,
        choices=Size.choices,
        default=Size.NA,
        verbose_name='Talla'
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Color'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad'
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

    class Meta:
        db_table = 'app_token_uniform_item'
        verbose_name = 'Item de Uniforme'
        verbose_name_plural = 'Items de Uniforme'

    def __str__(self):
        description = self.custom_description or self.get_item_type_display()
        return f"{description} - Talla: {self.get_size_display()} x {self.quantity}"

    @property
    def is_overdue(self):
        """Verifica si el item está vencido para devolución"""
        if not self.requires_return or not self.return_date or self.returned:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.return_date
