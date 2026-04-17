"""
Generador de PDF para Pautas usando pdfkit (wkhtmltopdf)
Sigue el mismo patron que el generador de tokens.
"""
import io
import base64
import logging
from datetime import datetime
from pathlib import Path

import qrcode
import pdfkit
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

PDFKIT_CONFIG = None


def get_pdfkit_config():
    global PDFKIT_CONFIG
    if PDFKIT_CONFIG is None:
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
    from PIL import Image

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e293b", back_color="white").convert('RGBA')

    if logo_path and Path(logo_path).exists():
        try:
            logo = Image.open(logo_path).convert('RGBA')
            qr_width, qr_height = qr_img.size
            logo_max_size = int(qr_width * 0.25)
            logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
            logo_bg_size = int(logo_max_size * 1.2)
            logo_bg = Image.new('RGBA', (logo_bg_size, logo_bg_size), (255, 255, 255, 255))
            logo_pos = ((logo_bg_size - logo.width) // 2, (logo_bg_size - logo.height) // 2)
            logo_bg.paste(logo, logo_pos, logo)
            pos_x = (qr_width - logo_bg_size) // 2
            pos_y = (qr_height - logo_bg_size) // 2
            qr_img.paste(logo_bg, (pos_x, pos_y), logo_bg)
        except Exception as e:
            logger.warning(f"No se pudo agregar logo al QR: {e}")

    qr_img = qr_img.convert('RGB')
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG', quality=100)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def get_image_base64(image_name: str) -> str:
    image_path = Path(settings.BASE_DIR) / 'static' / 'images' / image_name
    if image_path.exists():
        with open(image_path, 'rb') as f:
            img_str = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{img_str}"
    return ""


STATUS_CONFIGS = {
    'PENDING_PICKING': {'label': 'Pendiente de Picking', 'color': '#64748b', 'bg': '#f1f5f9'},
    'PICKING_ASSIGNED': {'label': 'Picker Asignado', 'color': '#2563eb', 'bg': '#dbeafe'},
    'PICKING_IN_PROGRESS': {'label': 'Picking en Progreso', 'color': '#2563eb', 'bg': '#dbeafe'},
    'PICKING_DONE': {'label': 'Picking Completado', 'color': '#2563eb', 'bg': '#dbeafe'},
    'IN_BAY': {'label': 'En Bahia', 'color': '#d97706', 'bg': '#fef3c7'},
    'PENDING_COUNT': {'label': 'Pendiente de Conteo', 'color': '#d97706', 'bg': '#fef3c7'},
    'COUNTING': {'label': 'En Conteo', 'color': '#d97706', 'bg': '#fef3c7'},
    'COUNTED': {'label': 'Contado', 'color': '#d97706', 'bg': '#fef3c7'},
    'PENDING_CHECKOUT': {'label': 'Pendiente de Checkout', 'color': '#7c3aed', 'bg': '#ede9fe'},
    'CHECKOUT_SECURITY': {'label': 'Checkout Seguridad', 'color': '#7c3aed', 'bg': '#ede9fe'},
    'CHECKOUT_OPS': {'label': 'Checkout Operaciones', 'color': '#7c3aed', 'bg': '#ede9fe'},
    'DISPATCHED': {'label': 'Despachado', 'color': '#059669', 'bg': '#d1fae5'},
    'CLOSED': {'label': 'Cerrada', 'color': '#64748b', 'bg': '#f1f5f9'},
    'CANCELLED': {'label': 'Cancelada', 'color': '#dc2626', 'bg': '#fee2e2'},
}


def generate_pauta_pdf(pauta) -> io.BytesIO:
    """Genera un PDF moderno para una pauta usando pdfkit."""
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    qr_url = f"{frontend_url}/truck-cycle/pautas/{pauta.id}"

    logo_qr_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo-qr.png'
    qr_data_url = generate_qr_base64(qr_url, str(logo_qr_path) if logo_qr_path.exists() else None)

    logo_base64 = get_image_base64('logo.png')
    status_config = STATUS_CONFIGS.get(pauta.status, STATUS_CONFIGS['PENDING_PICKING'])

    # Prepare timestamps
    timestamps = []
    for ts in pauta.timestamps.all().order_by('timestamp'):
        timestamps.append({
            'event_type_display': ts.get_event_type_display(),
            'timestamp': ts.timestamp,
            'recorded_by_name': ts.recorded_by.get_full_name() if ts.recorded_by else '-',
        })

    # Prepare assignments
    assignments = []
    for a in pauta.assignments.all():
        assignments.append({
            'role_display': a.get_role_display() if hasattr(a, 'get_role_display') else str(a.role),
            'personnel_name': a.personnel.full_name if a.personnel else '-',
            'assigned_by_name': a.assigned_by.get_full_name() if a.assigned_by else '-',
            'assigned_at': a.assigned_at,
            'is_active': a.is_active,
        })

    # Prepare inconsistencies
    inconsistencies = []
    for inc in pauta.inconsistencies.all():
        inconsistencies.append({
            'phase': inc.phase if hasattr(inc, 'phase') else '-',
            'inconsistency_type': inc.inconsistency_type if hasattr(inc, 'inconsistency_type') else '-',
            'product_name': inc.product_name if hasattr(inc, 'product_name') else '-',
            'expected_quantity': inc.expected_quantity if hasattr(inc, 'expected_quantity') else '-',
            'actual_quantity': inc.actual_quantity if hasattr(inc, 'actual_quantity') else '-',
            'difference': inc.difference if hasattr(inc, 'difference') else '-',
        })

    # Prepare checkout validation
    checkout_validation = None
    try:
        cv = pauta.checkout_validation
        if cv:
            checkout_validation = {
                'security_validated': cv.security_validated,
                'security_validator_name': cv.security_validator.full_name if cv.security_validator else None,
                'security_validated_at': cv.security_validated_at,
                'ops_validated': cv.ops_validated,
                'ops_validator_name': cv.ops_validator.full_name if cv.ops_validator else None,
                'ops_validated_at': cv.ops_validated_at,
            }
    except Exception:
        pass

    # Prepare bay assignment
    bay_assignment = None
    try:
        ba = pauta.bay_assignment
        if ba:
            bay_assignment = {
                'bay_code': ba.bay.code,
                'bay_name': ba.bay.name,
                'assigned_at': ba.assigned_at,
                'released_at': ba.released_at,
            }
    except Exception:
        pass

    context = {
        'pauta': pauta,
        'qr_data_url': qr_data_url,
        'logo_base64': logo_base64,
        'status_config': status_config,
        'generated_at': datetime.now(),
        'timestamps': timestamps,
        'assignments': assignments,
        'inconsistencies': inconsistencies,
        'checkout_validation': checkout_validation,
        'bay_assignment': bay_assignment,
    }

    html_content = render_to_string('truck_cycle/pauta_pdf.html', context)

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

    config = get_pdfkit_config()
    if config:
        pdf_bytes = pdfkit.from_string(html_content, False, options=options, configuration=config)
    else:
        pdf_bytes = pdfkit.from_string(html_content, False, options=options)

    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer
