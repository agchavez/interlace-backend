from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)
from datetime import datetime, timedelta
from django.conf import settings
import os
import uuid
from typing import Optional
from django.core.files.uploadedfile import File
from apps.document.models.document import DocumentModel


def get_sas_url(blob_name: str):
    # blob_name = "path/en/el/container/archivo.jpg"
    container_name = settings.AZURE_CONTAINER
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),  # Solo lectura
        expiry=datetime.utcnow() + timedelta(hours=1)  # Expira en 1 hora
    )

    # Arma la URL final
    return f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"


def create_documento(file_obj: File, name: Optional[str] = None, folder: str = "general",
                     subfolder: Optional[str] = None) -> DocumentModel:
    file_name = name if name else file_obj.name
    extension = ""
    if "." in file_name:
        extension = file_name.split(".")[-1].lower()

    doc_type = "other"
    if extension in ['jpg', 'jpeg', 'png', 'gif']:
        doc_type = "image"
    elif extension in ['pdf']:
        doc_type = "pdf"
    elif extension in ['doc', 'docx']:
        doc_type = "word"
    elif extension in ['xls', 'xlsx']:
        doc_type = "excel"

    # Crear el documento con los campos adecuados
    doc = DocumentModel(
        name=file_name,
        extension=extension,
        type=doc_type,
        folder=folder,
        subfolder=subfolder
    )

    # Generar nombre único para el archivo
    new_filename = f"{uuid.uuid4()}.{extension}" if extension else str(uuid.uuid4())

    # Crear ruta con estructura de carpetas
    if subfolder:
        new_path = f"document/{folder}/{subfolder}/{new_filename}"
    else:
        new_path = f"document/{folder}/{new_filename}"

    # Asignar el nombre al archivo antes de guardarlo
    file_obj.name = new_path
    doc.file = file_obj
    doc.save()

    return doc

