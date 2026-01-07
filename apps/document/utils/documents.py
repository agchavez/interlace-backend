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
from PIL import Image
from django.core.files.base import ContentFile
import io

from apps.document.utils.images import rotate_image_if_needed


def compress_image(image_file, quality=70):
    """
    image_file: InMemoryUploadedFile (u otro tipo de File) a comprimir
    Retorna un ContentFile comprimido (JPEG) con la misma extensión en el nombre.

    NOTA: Si la imagen ya es pequeña (< 1MB), se asume que ya fue comprimida
    en el frontend y no se comprime nuevamente para evitar doble compresión.
    """
    try:
        # Verificar el tamaño del archivo
        file_size_mb = image_file.size / (1024 * 1024)

        # Si la imagen es menor a 1MB, asumimos que ya fue comprimida en el frontend
        if file_size_mb < 1.0:
            print(f"Imagen ya comprimida ({file_size_mb:.2f}MB), se omite compresión en backend")
            image_file.seek(0)
            return image_file

        # Abre la imagen
        img = Image.open(image_file)

        # Si tiene transparencia, pasamos a RGB (pierdes transparencia si era PNG)
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGB")

        buffer = io.BytesIO()
        # Guardamos en JPEG por simplicidad, pero podrías condicionar a PNG/JPEG/WebP
        img.save(buffer, format='JPEG', optimize=True, quality=quality)
        buffer.seek(0)

        compressed_size_mb = len(buffer.getvalue()) / (1024 * 1024)
        print(f"Imagen comprimida en backend: {file_size_mb:.2f}MB → {compressed_size_mb:.2f}MB")

        # Retornamos un ContentFile que Django entienda
        compressed_file = ContentFile(buffer.read())
        # Mantén la extensión .jpg aunque el original sea .png si usas JPEG
        return compressed_file
    except Exception as e:
        # Si falla, retornas el archivo original sin compresión
        print(f"Error al comprimir imagen: {e}")
        image_file.seek(0)
        return image_file

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
    if doc_type == "image":
        rotated_file = rotate_image_if_needed(file_obj)  # quality=70 default
        compressed_file = compress_image(rotated_file)  # quality=70 default
        compressed_file.name = new_path  # Asigna la ruta final
        doc.file = compressed_file

        # Comprimir si es PDF
    # elif doc_type == "pdf":
    #     compressed_file = compress_pdf_ghostscript(file_obj)  # o compress_pdf_pikepdf(file_obj)
    #     compressed_file.name = new_path
    #     doc.file = compressed_file

    else:
        # Otros tipos de archivos, no se comprimen
        file_obj.name = new_path
        doc.file = file_obj
    doc.save()

    return doc

