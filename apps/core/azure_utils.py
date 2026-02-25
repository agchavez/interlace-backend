"""
Azure Storage utilities for generating SAS tokens
"""
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from django.conf import settings


def generate_blob_sas_url(blob_name: str, expiry_hours: int = 1) -> str:
    """
    Genera una URL con SAS token para acceder a un blob de Azure Storage

    Args:
        blob_name: Nombre del blob (ejemplo: "personnel/photos/2025/12/photo.jpg")
        expiry_hours: Horas de validez del token (default: 1 hora)

    Returns:
        URL completa con SAS token
    """
    if not blob_name:
        return None

    try:
        # Sanitizar la clave: eliminar espacios/saltos de línea que corrompen el Base64
        account_key = settings.AZURE_ACCOUNT_KEY.strip()

        # Generar SAS token
        sas_token = generate_blob_sas(
            account_name=settings.AZURE_ACCOUNT_NAME,
            account_key=account_key,
            container_name=settings.AZURE_CONTAINER,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
        )

        # Construir URL completa
        blob_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{blob_name}?{sas_token}"

        return blob_url

    except Exception as e:
        # En caso de error, retornar None
        print(f"Error generando SAS token para {blob_name}: {str(e)}")
        return None


def get_blob_name_from_url(url: str) -> str:
    """
    Extrae el nombre del blob de una URL de Azure Storage

    Args:
        url: URL del blob (ejemplo: "https://account.blob.core.windows.net/container/path/file.jpg")

    Returns:
        Nombre del blob (ejemplo: "path/file.jpg")
    """
    if not url:
        return None

    try:
        # Remover el dominio y el contenedor
        # Formato: https://{account}.blob.core.windows.net/{container}/{blob_name}
        parts = url.split(f"{settings.AZURE_CONTAINER}/")
        if len(parts) > 1:
            # Remover query parameters si existen
            blob_name = parts[1].split('?')[0]
            return blob_name
        return None
    except Exception:
        return None


def get_photo_url_with_sas(photo_field) -> str:
    """
    Genera URL con SAS token para un campo de foto (FileField/ImageField)

    Args:
        photo_field: Campo FileField/ImageField de Django

    Returns:
        URL con SAS token o None si no hay foto
    """
    if not photo_field:
        return None

    try:
        # Obtener el nombre del blob
        blob_name = photo_field.name

        # Generar URL con SAS token (válido por 2 horas)
        return generate_blob_sas_url(blob_name, expiry_hours=2)

    except Exception as e:
        print(f"Error generando URL con SAS token: {str(e)}")
        return None
