
from django.db import models

from utils import BaseModel


class DocumentModel(BaseModel):
    """
    Modelo que representa un documento/archivo almacenado en Azure Blob Storage.
    Usar FileField (o ImageField) para guardar la ruta.
    """
    name = models.CharField(max_length=255)
    file = models.FileField(
        upload_to="document/",   # subcarpeta en tu contenedor
        blank=True,
        null=True
    )
    extension = models.CharField(max_length=10, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "app_document"
        verbose_name = "Document"
        verbose_name_plural = ""

    def save(self, *args, **kwargs):
        """Sobrescribir para, por ejemplo, extraer extension, mime-type, etc."""
        if self.file and not self.extension:
            # Ejemplo simple para extraer extensión
            filename = self.file.name  # "documentos/loquesea.png"
            if "." in filename:
                self.extension = filename.split(".")[-1].lower()
        super().save(*args, **kwargs)
