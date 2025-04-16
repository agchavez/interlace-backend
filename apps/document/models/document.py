import uuid
from django.db import models
from utils import BaseModel


def document_upload_path(instance, filename):
    """
    Devuelve la ruta donde se almacenará el archivo, usando la estructura:
      document/<folder>[/<subfolder>]/<unique_name>.<extension>
    """
    # Usa los campos del modelo en lugar de atributos temporales
    folder = instance.folder or "general"
    subfolder = instance.subfolder or ""

    extension = filename.split('.')[-1].lower() if '.' in filename else ""
    unique_name = f"{uuid.uuid4()}.{extension}" if extension else str(uuid.uuid4())

    if subfolder:
        return f"document/{folder}/{subfolder}/{unique_name}"
    else:
        return f"document/{folder}/{unique_name}"


class DocumentModel(BaseModel):
    """
    Modelo que representa un documento/archivo almacenado en Azure Blob Storage.
    Se utilizará la función 'document_upload_path' para definir la ruta de almacenamiento.
    """
    name = models.CharField(max_length=255)
    file = models.FileField(
        upload_to=document_upload_path,  # Usamos la función callable
        blank=True,
        null=True
    )
    extension = models.CharField(max_length=10, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    folder = models.CharField(max_length=50, default="general")
    subfolder = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "app_document"
        verbose_name = "Document"
        verbose_name_plural = ""

    def save(self, *args, **kwargs):
        if self.file and not self.extension:
            filename = self.file.name
            if "." in filename:
                self.extension = filename.split(".")[-1].lower()
        super().save(*args, **kwargs)