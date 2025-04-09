# reclamos/models.py
from django.db import models
from django.conf import settings

from apps.document.models.document import DocumentModel
from apps.tracker.models import TrackerModel
from apps.maintenance.models.product import ProductModel
from utils import BaseModel

# Nuevas opciones para el tipo de reclamo
CLAIM_TYPE_CHOICES = (
    ("FALTANTE", "Faltante"),
    ("SOBRANTE", "Sobrante"),
    ("DAÑOS_CALIDAD_TRANSPORTE", "Daños por Calidad y Transporte"),
)

# Opciones para el estado del reclamo
CLAIM_STATUS_CHOICES = (
    ("PENDIENTE", "Pendiente"),
    ("EN_REVISION", "En Revisión"),
    ("RECHAZADO", "Rechazado"),
    ("APROBADO", "Aprobado"),
)

# TYPE
TYPES_CLAIM = {
    "CLAIM": "Claim",
    "ALERT_QUALITY": "ALERT_QUALITY",
}

# Modelo para tipos de reclamos
class ClaimTypeModel(BaseModel):
    """
    Modelo para los tipos de reclamos.
    """
    name = models.CharField("Nombre", max_length=50, unique=True)
    description = models.TextField("Descripción", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "app_claim_type"
        verbose_name = "Tipo de Reclamo"
        verbose_name_plural = "Tipos de Reclamos"

class ClaimModel(BaseModel):
    """
    Modelo para reclamos de productos, con carga de documentos en diversas categorías.
    """
    tracker = models.OneToOneField(
        TrackerModel,
        on_delete=models.CASCADE,
        related_name="claim",
        verbose_name="Tracker asociado"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claims_assigned",
        verbose_name="Asignado a"
    )

    type = models.CharField(
        "Tipo",
        max_length=50,
        choices=TYPES_CLAIM.items(),
        default="CLAIM"
    )

    claim_type = models.ForeignKey(
        ClaimTypeModel,
        on_delete=models.CASCADE,
        related_name="claims",
        verbose_name="Tipo de Reclamo",
        blank=True,
        null=True
    )

    description = models.TextField("Descripción del Reclamo", null=True, blank=True)
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=CLAIM_STATUS_CHOICES,
        default="PENDIENTE"
    )

    # Campos para la información general del reclamo
    claim_number = models.CharField(
        "Número de Claim",
        max_length=50,
        blank=True,
        null=True
    )
    claim_file = models.FileField(
        "Archivo Claim (PDF o Excel)",
        upload_to="claim_files/",
        blank=True,
        null=True
    )

    production_batch_file = models.FileField(
        "Archivo de Lotes de Producción (PDF)",
        upload_to="claim_production_batches/",
        blank=True,
        null=True
    )
    credit_memo_file = models.FileField(
        "Nota de Crédito",
        upload_to="claim_credit_memos/",
        blank=True,
        null=True
    )
    discard_doc = models.CharField(
        "Documento de Descarte",
        max_length=100,
        blank=True,
        null=True
    )
    observations = models.TextField("Observaciones", blank=True, null=True)
    observations_file = models.FileField(
        "Archivo de Observaciones (PDF)",
        upload_to="claim_observations/",
        blank=True,
        null=True
    )

    # Campos para Fotografías (cada campo puede tener hasta 5 documentos)
    photos_container_closed = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_container_closed",
        verbose_name="Fotografías: Contenedor cerrado"
    )
    photos_container_one_open = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_container_one_open",
        verbose_name="Fotografías: Contenedor con 1 puerta abierta"
    )
    photos_container_two_open = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_container_two_open",
        verbose_name="Fotografías: Contenedor con 2 puertas abiertas"
    )
    photos_container_top = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_container_top",
        verbose_name="Fotografías: Vista superior del contenido"
    )
    photos_during_unload = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_during_unload",
        verbose_name="Fotografías: Durante la descarga"
    )
    photos_pallet_damage = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_pallet_damage",
        verbose_name="Fotografías: Fisuras/abolladuras de pallets"
    )
    # Fotografías de producto dañado, subdividido en:
    photos_damaged_product_base = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_damaged_product_base",
        verbose_name="Fotografías: Base de lata/botella dañada"
    )
    photos_damaged_product_dents = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_damaged_product_dents",
        verbose_name="Fotografías: Abolladuras del producto"
    )
    photos_damaged_boxes = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_damaged_boxes",
        verbose_name="Fotografías: Cajas dañadas"
    )
    photos_grouped_bad_product = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_grouped_bad_product",
        verbose_name="Fotografías: Producto en mal estado agrupado"
    )
    photos_repalletized = models.ManyToManyField(
        DocumentModel,
        blank=True,
        related_name="claims_repalletized",
        verbose_name="Fotografías: Repaletizado de producto dañado"
    )

    claim_code = models.CharField("Código de Claim", max_length=20, blank=True, null=True)

    reject_reason = models.CharField("Razón de Rechazo", max_length=150, blank=True, null=True)

    approve_observations = models.TextField("Observaciones de Aprobación", blank=True, null=True)

    def __str__(self):
        return f"Claim #{self.id} - {self.claim_type} [{self.status}]"

    def save(self, *args, **kwargs):
        # Guardamos normalmente para asignar el id
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Si es nuevo y aún no se generó el claim_code, lo generamos
        if is_new and not self.claim_code:
            self.claim_code = f"CLM-{self.id:05d}"
            # Actualizamos solo el campo claim_code para evitar un bucle infinito
            super().save(update_fields=["claim_code"])


    class Meta:
        db_table = "app_claim"
        verbose_name = "Claim"
        verbose_name_plural = "Claims"

# Productos asociados al reclamo
class ClaimProductModel(BaseModel):
    """
    Modelo para asociar productos a un reclamo.
    """
    claim = models.ForeignKey(
        ClaimModel,
        on_delete=models.CASCADE,
        related_name="claim_products",
        verbose_name="Reclamo asociado"
    )
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name="claim_products",
        verbose_name="Producto asociado"
    )

    quantity = models.IntegerField("Cantidad", default=0)

    batch = models.CharField(
        "Lote",
        max_length=50,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Claim #{self.claim.id} - Producto: {self.product.name} ({self.quantity})"

    class Meta:
        db_table = "app_claim_product"
        verbose_name = "Producto del Claim"
        verbose_name_plural = "Productos del Claim"

