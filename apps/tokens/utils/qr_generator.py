"""
Utilidad para generar códigos QR de tokens
"""
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


def generate_token_qr(token_request):
    """
    Genera un código QR para un token y lo sube a Azure Blob Storage.

    Args:
        token_request: Instancia de TokenRequest

    Returns:
        str: URL del código QR generado
    """
    # Construir la URL pública del token
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    public_url = f"{frontend_url}/public/token/{token_request.token_code}"

    # Configurar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alto nivel de corrección para logo
        box_size=10,
        border=4,
    )
    qr.add_data(public_url)
    qr.make(fit=True)

    # Crear imagen
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir a bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Nombre del archivo en storage
    blob_name = f"tokens/qr/{token_request.token_code}.png"

    try:
        # Guardar en el storage configurado (Azure Blob)
        file_name = default_storage.save(
            blob_name,
            ContentFile(buffer.read())
        )

        # Obtener URL del archivo
        qr_url = default_storage.url(file_name)

        logger.info(f"QR generado para token {token_request.display_number}: {qr_url}")
        return qr_url

    except Exception as e:
        logger.error(f"Error al guardar QR en storage: {e}")
        # Fallback: retornar URL sin verificar que existe
        azure_url = getattr(settings, 'MEDIA_URL', '')
        return f"{azure_url}{blob_name}"


def generate_qr_image_bytes(url):
    """
    Genera los bytes de un código QR para una URL dada.
    Útil para generar QR en memoria sin guardar.

    Args:
        url: URL a codificar en el QR

    Returns:
        bytes: Imagen PNG del QR en bytes
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer.getvalue()
