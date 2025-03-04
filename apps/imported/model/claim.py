# reclamos/models.py
from django.db import models
from django.conf import settings

from apps.document.models.document import DocumentModel
from apps.tracker.models import TrackerModel
from utils import BaseModel

TIPO_RECLAMO_CHOICES = (
    ("DAÑOS", "Daños en la Mercancía"),
    ("FALTANTES", "Faltantes"),
    ("TIEMPOS", "Tiempos de Entrega"),
    ("OTRO", "Otro"),
)

ESTADO_RECLAMO_CHOICES = (
    ("PENDIENTE", "Pendiente"),
    ("EN_PROCESO", "En proceso"),
    ("RESUELTO", "Resuelto"),
    ("CERRADO", "Cerrado"),
)

class ClaimModel(BaseModel):
    """
    Reclamo asociado a un Tracker, con 4 campos
    (uno para cada documento/imágen).
    """
    tracker = models.ForeignKey(
        TrackerModel,
        on_delete=models.CASCADE,
        related_name="reclamos",
        verbose_name="Tracker asociado"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamos_asignados",
        verbose_name="Asignado a"
    )

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_RECLAMO_CHOICES,
        default="OTRO"
    )
    descripcion = models.TextField("Descripción del reclamo")

    status = models.CharField(
        max_length=20,
        choices=ESTADO_RECLAMO_CHOICES,
        default="PENDIENTE"
    )

    # Cuatro referencias a DocumentoModel
    doc_trailer = models.ForeignKey(
        DocumentModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamos_trailer",
        verbose_name="Documento del Tráiler"
    )
    doc_descarga = models.ForeignKey(
        DocumentModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamos_descarga",
        verbose_name="Documento de Descarga"
    )
    doc_contenido = models.ForeignKey(
        DocumentModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamos_contenido",
        verbose_name="Documento del Contenido"
    )
    doc_producto = models.ForeignKey(
        DocumentModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamos_producto",
        verbose_name="Documento del Producto"
    )

    def __str__(self):
        return f"Reclamo #{self.id} - {self.tipo} [{self.status}]"

    class Meta:
        db_table = "app_claim"
        verbose_name = "Claim"
        verbose_name_plural = "Claims"
