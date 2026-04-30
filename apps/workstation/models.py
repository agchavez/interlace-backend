"""
Modelos del módulo Workstation.

El layout de cada Workstation se compone de **bloques** posicionables en una
grilla de 12 columnas (drag & drop en el editor). Cada bloque tiene un `type`
(determinado por una lista cerrada) y un `config` JSON con la data específica.
"""
import uuid

from django.db import models

from utils.BaseModel import BaseModel


def workstation_doc_upload_path(instance, filename):
    """Ruta en Azure Blob: workstation/<ws_id>/docs/<uuid>.<ext>"""
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    unique_name = f'{uuid.uuid4()}.{extension}' if extension else str(uuid.uuid4())
    return f'workstation/{instance.workstation_id}/docs/{unique_name}'


def workstation_image_upload_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    unique_name = f'{uuid.uuid4()}.{extension}' if extension else str(uuid.uuid4())
    return f'workstation/{instance.workstation_id}/images/{unique_name}'


class Workstation(BaseModel):
    """Estación de trabajo configurable. Una por combinación (CD, rol)."""
    ROLE_PICKING = 'PICKING'
    ROLE_PICKER = 'PICKER'
    ROLE_COUNTER = 'COUNTER'
    ROLE_YARD = 'YARD'
    ROLE_REPACK = 'REPACK'
    ROLE_CHOICES = [
        (ROLE_PICKING, 'Picking (legacy)'),
        (ROLE_PICKER, 'Picker'),
        (ROLE_COUNTER, 'Contador'),
        (ROLE_YARD, 'Chofer de Patio'),
        (ROLE_REPACK, 'Reempaque'),
    ]

    distributor_center = models.ForeignKey(
        'maintenance.DistributorCenter',
        on_delete=models.CASCADE,
        related_name='workstations',
        verbose_name='Centro de Distribución',
    )
    role = models.CharField('Rol', max_length=10, choices=ROLE_CHOICES)
    name = models.CharField('Nombre', max_length=80, blank=True, default='')
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        db_table = 'workstation'
        verbose_name = 'Estación de Trabajo'
        verbose_name_plural = 'Estaciones de Trabajo'
        unique_together = ['distributor_center', 'role']
        ordering = ['distributor_center__name', 'role']

    def __str__(self):
        label = self.name or self.get_role_display()
        return f'{self.distributor_center.name} · {label}'


# ────────── Catálogos master (mismos para todos los CDs) ──────────

class RiskCatalog(models.Model):
    """Catálogo maestro de riesgos del área."""
    code = models.SlugField('Código', max_length=40, unique=True)
    name = models.CharField('Nombre', max_length=80)
    icon_name = models.CharField(
        'Ícono Material UI', max_length=60,
        help_text='Nombre del ícono MUI, ej: DirectionsRun, ContentCut',
    )
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        db_table = 'workstation_risk_catalog'
        verbose_name = 'Catálogo · Riesgo'
        verbose_name_plural = 'Catálogo · Riesgos'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProhibitionCatalog(models.Model):
    """Catálogo maestro de prohibiciones del área."""
    code = models.SlugField('Código', max_length=40, unique=True)
    name = models.CharField('Nombre', max_length=80)
    icon_name = models.CharField(
        'Ícono Material UI', max_length=60,
        help_text='Nombre del ícono MUI, ej: Fastfood, SmokingRooms',
    )
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        db_table = 'workstation_prohibition_catalog'
        verbose_name = 'Catálogo · Prohibición'
        verbose_name_plural = 'Catálogo · Prohibiciones'
        ordering = ['name']

    def __str__(self):
        return self.name


# ────────── Imagen subida (referenciada por bloques IMAGE) ──────────

class WorkstationImage(BaseModel):
    """Imagen subida para usar en un bloque IMAGE del layout."""
    workstation = models.ForeignKey(
        Workstation, on_delete=models.CASCADE, related_name='images',
    )
    name = models.CharField('Nombre', max_length=160, blank=True, default='')
    file = models.ImageField('Archivo', upload_to=workstation_image_upload_path)
    alt = models.CharField('Texto alternativo', max_length=160, blank=True, default='')

    class Meta:
        db_table = 'workstation_image'
        verbose_name = 'Imagen de Estación'
        verbose_name_plural = 'Imágenes de Estación'
        ordering = ['workstation', '-created_at']


# ────────── Documentos (PDFs accesibles por QR con login) ──────────

class WorkstationDocument(BaseModel):
    """Documento PDF accesible vía QR (token UUID + login Interlace)."""
    DOC_SOP = 'SOP'
    DOC_OPL = 'OPL'
    DOC_OTHER = 'OTHER'
    DOC_CHOICES = [
        (DOC_SOP, 'SOP — Standard Operating Procedure'),
        (DOC_OPL, 'OPL — One Point Lesson'),
        (DOC_OTHER, 'Otro'),
    ]

    workstation = models.ForeignKey(
        Workstation, on_delete=models.CASCADE, related_name='documents',
    )
    doc_type = models.CharField('Tipo', max_length=10, choices=DOC_CHOICES, default=DOC_SOP)
    name = models.CharField('Nombre', max_length=160)
    file = models.FileField('Archivo PDF', upload_to=workstation_doc_upload_path)
    qr_token = models.UUIDField('Token QR', default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        db_table = 'workstation_document'
        verbose_name = 'Documento de Estación'
        verbose_name_plural = 'Documentos de Estación'
        ordering = ['workstation', 'doc_type', '-created_at']

    def __str__(self):
        return f'{self.workstation} · {self.doc_type} · {self.name}'


# ────────── Bloques del layout (núcleo del editor drag & drop) ──────────

class WorkstationBlock(BaseModel):
    """
    Bloque dentro del layout de una Workstation. Posicionado en grilla 12 cols.

    Tipos:
      - RISKS: pinta los riesgos del catálogo seleccionados.
        config = { "catalog_ids": [int], "title": str? }
      - PROHIBITIONS: pinta las prohibiciones del catálogo seleccionadas.
        config = { "catalog_ids": [int], "title": str? }
      - TRIGGERS: tabla de KPIs/metas/disparadores (data inline).
        config = { "title": str?, "items": [{indicator, meta, disparador, unit?}, ...] }
      - SIC_CHART: gráfico SIC con tabs por KPI.
        config = { "title": str?, "kpis": [{label, ranges:{green, yellow, red}}], "default_index": int? }
      - REACTION_PLANS: bloque compuesto con caja amarilla + roja + QR opcional.
        config = {
          "title": str?, "kpi_label": str,
          "yellow": {"title": str, "description": str, "qr_url"?: str, "qr_label"?: str},
          "red":    {"title": str, "description": str},
        }
      - QR_DOCUMENT: QR a un PDF subido (referencia WorkstationDocument).
        config = { "document_id": int, "title": str?, "show_label": bool? }
      - QR_EXTERNAL: QR a una URL externa.
        config = { "url": str, "title": str?, "label": str? }
      - IMAGE: imagen subida (referencia WorkstationImage).
        config = { "image_id": int, "fit": "contain"|"cover", "title": str? }
      - TEXT: texto libre con estilo.
        config = { "content": str, "size": "small"|"medium"|"large", "align": "left"|"center"|"right" }
      - TITLE: título grande.
        config = { "content": str }
      - CLOCK: reloj actual (HN).
        config = { "show_date": bool? }
      - DPO: card "DPO · Es el camino" (decorativo).
        config = {}
    """
    TYPE_RISKS = 'RISKS'
    TYPE_PROHIBITIONS = 'PROHIBITIONS'
    TYPE_TRIGGERS = 'TRIGGERS'
    TYPE_SIC_CHART = 'SIC_CHART'
    TYPE_REACTION_PLANS = 'REACTION_PLANS'
    TYPE_QR_DOCUMENT = 'QR_DOCUMENT'
    TYPE_QR_EXTERNAL = 'QR_EXTERNAL'
    TYPE_IMAGE = 'IMAGE'
    TYPE_TEXT = 'TEXT'
    TYPE_TITLE = 'TITLE'
    TYPE_CLOCK = 'CLOCK'
    TYPE_DPO = 'DPO'
    TYPE_CHOICES = [
        (TYPE_RISKS,         'Riesgos del área'),
        (TYPE_PROHIBITIONS,  'Prohibiciones del área'),
        (TYPE_TRIGGERS,      'Disparador resolución de problemas'),
        (TYPE_SIC_CHART,     'SIC / Pi Crítico'),
        (TYPE_REACTION_PLANS,'Planes de Reacción'),
        (TYPE_QR_DOCUMENT,   'QR · Documento PDF'),
        (TYPE_QR_EXTERNAL,   'QR · Link externo'),
        (TYPE_IMAGE,         'Imagen'),
        (TYPE_TEXT,          'Texto / Nota'),
        (TYPE_TITLE,         'Título'),
        (TYPE_CLOCK,         'Reloj'),
        (TYPE_DPO,           'Sello DPO'),
    ]

    workstation = models.ForeignKey(
        Workstation, on_delete=models.CASCADE, related_name='blocks',
    )
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    config = models.JSONField('Configuración', default=dict, blank=True)

    # Posición grid (12 cols).
    grid_x = models.PositiveIntegerField('X', default=0)
    grid_y = models.PositiveIntegerField('Y', default=0)
    grid_w = models.PositiveIntegerField('Ancho', default=4)
    grid_h = models.PositiveIntegerField('Alto', default=3)

    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        db_table = 'workstation_block'
        verbose_name = 'Bloque'
        verbose_name_plural = 'Bloques'
        ordering = ['workstation', 'grid_y', 'grid_x']

    def __str__(self):
        return f'{self.workstation} · {self.get_type_display()}'
