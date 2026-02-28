"""
Generador de PDF para Tokens usando pdfkit (wkhtmltopdf)
Renderiza HTML moderno a PDF de alta calidad.
"""
import io
import base64
import qrcode
import logging
import pdfkit
from datetime import datetime
from pathlib import Path

from django.template.loader import render_to_string
from django.conf import settings

from ..models import TokenRequest

logger = logging.getLogger(__name__)

# Configuración de wkhtmltopdf
PDFKIT_CONFIG = None


def get_pdfkit_config():
    """Obtiene la configuración de pdfkit con la ruta de wkhtmltopdf."""
    global PDFKIT_CONFIG
    if PDFKIT_CONFIG is None:
        # Rutas comunes de wkhtmltopdf en Windows
        possible_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            getattr(settings, 'WKHTMLTOPDF_PATH', ''),
        ]
        for path in possible_paths:
            if path and Path(path).exists():
                PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=path)
                break
    return PDFKIT_CONFIG


def generate_qr_base64(data: str, logo_path: str = None) -> str:
    """Genera un código QR con logo en el centro y lo retorna como data URL base64."""
    from PIL import Image

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta corrección para permitir logo
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e293b", back_color="white").convert('RGBA')

    # Agregar logo en el centro si existe
    if logo_path and Path(logo_path).exists():
        try:
            logo = Image.open(logo_path).convert('RGBA')

            # Calcular tamaño del logo (25% del QR)
            qr_width, qr_height = qr_img.size
            logo_max_size = int(qr_width * 0.25)

            # Redimensionar logo manteniendo proporción
            logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)

            # Crear fondo blanco circular/cuadrado para el logo
            logo_bg_size = int(logo_max_size * 1.2)
            logo_bg = Image.new('RGBA', (logo_bg_size, logo_bg_size), (255, 255, 255, 255))

            # Centrar logo en el fondo
            logo_pos = ((logo_bg_size - logo.width) // 2, (logo_bg_size - logo.height) // 2)
            logo_bg.paste(logo, logo_pos, logo)

            # Posición central en el QR
            pos_x = (qr_width - logo_bg_size) // 2
            pos_y = (qr_height - logo_bg_size) // 2

            # Pegar logo con fondo en el QR
            qr_img.paste(logo_bg, (pos_x, pos_y), logo_bg)
        except Exception as e:
            logger.warning(f"No se pudo agregar logo al QR: {e}")

    # Convertir a RGB para guardar como PNG
    qr_img = qr_img.convert('RGB')

    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG', quality=100)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def get_image_base64(image_name: str) -> str:
    """Obtiene una imagen como base64."""
    image_path = Path(settings.BASE_DIR) / 'static' / 'images' / image_name
    if image_path.exists():
        with open(image_path, 'rb') as f:
            img_str = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{img_str}"
    return ""


def get_status_config(status: str) -> dict:
    """Retorna la configuración visual según el estado (sin emojis)."""
    configs = {
        'DRAFT': {'label': 'Borrador', 'color': '#64748b', 'bg': '#f1f5f9'},
        'PENDING_L1': {'label': 'Pendiente Nivel 1', 'color': '#d97706', 'bg': '#fef3c7'},
        'PENDING_L2': {'label': 'Pendiente Nivel 2', 'color': '#d97706', 'bg': '#fef3c7'},
        'PENDING_L3': {'label': 'Pendiente Nivel 3', 'color': '#d97706', 'bg': '#fef3c7'},
        'APPROVED': {'label': 'Aprobado', 'color': '#059669', 'bg': '#d1fae5'},
        'USED': {'label': 'Utilizado', 'color': '#2563eb', 'bg': '#dbeafe'},
        'EXPIRED': {'label': 'Expirado', 'color': '#64748b', 'bg': '#f1f5f9'},
        'CANCELLED': {'label': 'Cancelado', 'color': '#dc2626', 'bg': '#fee2e2'},
        'REJECTED': {'label': 'Rechazado', 'color': '#dc2626', 'bg': '#fee2e2'},
    }
    return configs.get(status, configs['DRAFT'])


def generate_token_pdf(token: TokenRequest) -> io.BytesIO:
    """
    Genera un PDF moderno para un token usando pdfkit.
    """
    # Preparar datos
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    qr_url = f"{frontend_url}/public/token/{token.token_code}"

    # Ruta del logo para el QR
    logo_qr_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo-qr.png'
    qr_data_url = generate_qr_base64(qr_url, str(logo_qr_path) if logo_qr_path.exists() else None)

    # Cargar imágenes
    logo_base64 = get_image_base64('logo.png')
    logo_qr_base64 = get_image_base64('logo-qr.png')

    status_config = get_status_config(token.status)

    # Nombre del solicitante
    requested_by_name = "-"
    if token.requested_by:
        name = f"{token.requested_by.first_name} {token.requested_by.last_name}".strip()
        requested_by_name = name or token.requested_by.email

    # Datos del beneficiario (persona interna o externa)
    if token.personnel:
        beneficiary_name = token.personnel.full_name
        beneficiary_code = token.personnel.employee_code or "-"
        beneficiary_area = token.personnel.area.name if token.personnel.area else "-"
        beneficiary_position = token.personnel.position or "-"
        is_external_beneficiary = False
    else:
        is_external_beneficiary = True
        beneficiary_code = "-"
        beneficiary_area = "-"
        beneficiary_position = "-"
        try:
            ep = token.exit_pass_detail.external_person
            beneficiary_name = ep.name if ep else "Persona Externa"
            beneficiary_code = ep.identification if ep else "-"
            beneficiary_area = ep.company if ep else "-"
        except Exception:
            beneficiary_name = "Persona Externa"

    # Obtener código de país del centro de distribución
    country_code = 'hn'  # Default Honduras
    try:
        if token.distributor_center and token.distributor_center.country:
            country_code = token.distributor_center.country.code.lower()
    except Exception:
        pass

    # Contexto para el template
    context = {
        'token': token,
        'qr_data_url': qr_data_url,
        'logo_base64': logo_base64,
        'logo_qr_base64': logo_qr_base64,
        'status_config': status_config,
        'generated_at': datetime.now(),
        'requested_by_name': requested_by_name,
        'country_code': country_code,
        'beneficiary_name': beneficiary_name,
        'beneficiary_code': beneficiary_code,
        'beneficiary_area': beneficiary_area,
        'beneficiary_position': beneficiary_position,
        'is_external_beneficiary': is_external_beneficiary,
    }

    # Agregar detalles específicos del tipo
    detail_attrs = {
        'PERMIT_HOUR': 'permit_hour_detail',
        'PERMIT_DAY': 'permit_day_detail',
        'EXIT_PASS': 'exit_pass_detail',
        'UNIFORM_DELIVERY': 'uniform_delivery_detail',
        'OVERTIME': 'overtime_detail',
        'SHIFT_CHANGE': 'shift_change_detail',
        'SUBSTITUTION': 'substitution_detail',
        'RATE_CHANGE': 'rate_change_detail',
    }

    detail_attr = detail_attrs.get(token.token_type)
    if detail_attr:
        try:
            detail = getattr(token, detail_attr, None)
            if detail:
                context[detail_attr] = detail
                if hasattr(detail, 'items'):
                    context[f'{detail_attr}_items'] = detail.items.all()
        except Exception:
            pass

    # Renderizar HTML
    html_content = render_to_string('tokens/token_pdf.html', context)

    # Opciones de PDF
    options = {
        'page-size': 'Letter',
        'margin-top': '0.4in',
        'margin-right': '0.4in',
        'margin-bottom': '0.4in',
        'margin-left': '0.4in',
        'encoding': 'UTF-8',
        'enable-local-file-access': None,
        'print-media-type': None,
        'no-stop-slow-scripts': None,
        'image-quality': '100',
        'image-dpi': '300',
    }

    # Generar PDF
    config = get_pdfkit_config()
    if config:
        pdf_bytes = pdfkit.from_string(html_content, False, options=options, configuration=config)
    else:
        pdf_bytes = pdfkit.from_string(html_content, False, options=options)

    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer


def get_token_type_label(token_type: str) -> str:
    """Retorna la etiqueta legible del tipo de token."""
    labels = {
        'PERMIT_HOUR': 'Permiso por Hora',
        'PERMIT_DAY': 'Permiso por Día',
        'EXIT_PASS': 'Pase de Salida',
        'UNIFORM_DELIVERY': 'Entrega de Uniforme',
        'SUBSTITUTION': 'Sustitución',
        'RATE_CHANGE': 'Cambio de Tasa',
        'OVERTIME': 'Horas Extra',
        'SHIFT_CHANGE': 'Cambio de Turno',
    }
    return labels.get(token_type, token_type)


def generate_token_receipt(token: TokenRequest, is_copy: bool = False) -> io.BytesIO:
    """
    Genera un recibo tipo ticket (80mm) para impresoras térmicas.
    Solo disponible cuando el token está en estado final (APPROVED, USED).

    Args:
        token: El token a generar recibo
        is_copy: True para marcar como COPIA, False para ORIGINAL
    """
    # Verificar que el token esté en estado final
    final_states = [
        TokenRequest.Status.APPROVED,
        TokenRequest.Status.USED,
    ]
    if token.status not in final_states:
        raise ValueError(f"El recibo solo está disponible para tokens aprobados o utilizados. Estado actual: {token.get_status_display()}")

    # Preparar datos
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    qr_url = f"{frontend_url}/public/token/{token.token_code}"

    # Ruta del logo para el QR (más pequeño para el recibo)
    logo_qr_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo-qr.png'
    qr_data_url = generate_qr_base64(qr_url, str(logo_qr_path) if logo_qr_path.exists() else None)

    status_config = get_status_config(token.status)

    # Nombre del solicitante
    requested_by_name = "-"
    if token.requested_by:
        name = f"{token.requested_by.first_name} {token.requested_by.last_name}".strip()
        requested_by_name = name or token.requested_by.email

    # Datos del beneficiario (persona interna o externa)
    if token.personnel:
        beneficiary_name = token.personnel.full_name
        beneficiary_code = token.personnel.employee_code or "-"
        beneficiary_area = token.personnel.area.name if token.personnel.area else "-"
        is_external_beneficiary = False
    else:
        is_external_beneficiary = True
        beneficiary_code = "-"
        beneficiary_area = "-"
        try:
            ep = token.exit_pass_detail.external_person
            beneficiary_name = ep.name if ep else "Persona Externa"
            beneficiary_code = ep.identification if ep else "-"
            beneficiary_area = ep.company if ep else "-"
        except Exception:
            beneficiary_name = "Persona Externa"

    # Contexto para el template
    context = {
        'token': token,
        'qr_data_url': qr_data_url,
        'status_config': status_config,
        'generated_at': datetime.now(),
        'is_copy': is_copy,
        'token_type_label': get_token_type_label(token.token_type),
        'requested_by_name': requested_by_name,
        'beneficiary_name': beneficiary_name,
        'beneficiary_code': beneficiary_code,
        'beneficiary_area': beneficiary_area,
        'is_external_beneficiary': is_external_beneficiary,
    }

    # Agregar detalles específicos del tipo
    detail_attrs = {
        'PERMIT_HOUR': 'permit_hour_detail',
        'PERMIT_DAY': 'permit_day_detail',
        'EXIT_PASS': 'exit_pass_detail',
        'UNIFORM_DELIVERY': 'uniform_delivery_detail',
        'OVERTIME': 'overtime_detail',
        'SHIFT_CHANGE': 'shift_change_detail',
        'SUBSTITUTION': 'substitution_detail',
        'RATE_CHANGE': 'rate_change_detail',
    }

    detail_attr = detail_attrs.get(token.token_type)
    if detail_attr:
        try:
            detail = getattr(token, detail_attr, None)
            if detail:
                context[detail_attr] = detail
                if hasattr(detail, 'items'):
                    context[f'{detail_attr}_items'] = detail.items.all()
        except Exception:
            pass

    # Renderizar HTML
    html_content = render_to_string('tokens/token_receipt.html', context)

    # Opciones de PDF para recibo térmico (80mm width)
    # Usar altura automática para evitar saltos de página
    options = {
        'page-width': '80mm',
        'page-height': '297mm',  # Altura de A4, el contenido define la longitud real
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': 'UTF-8',
        'enable-local-file-access': None,
        'print-media-type': None,
        'no-stop-slow-scripts': None,
        'image-quality': '100',
        'dpi': '203',  # DPI típico de impresoras térmicas
        'disable-smart-shrinking': None,
        'no-pdf-compression': None,
    }

    # Generar PDF
    config = get_pdfkit_config()
    if config:
        pdf_bytes = pdfkit.from_string(html_content, False, options=options, configuration=config)
    else:
        pdf_bytes = pdfkit.from_string(html_content, False, options=options)

    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer
