"""
Templates default de bloques al crear una Workstation.

Cada rol tiene una distribución y configuración propia que aproxima al PPT
del cliente. El usuario puede modificarla libremente desde el editor.

Grilla de 12 columnas. Las 4 estaciones comparten la base (Riesgos /
Prohibiciones / Disparadores arriba, SIC + Planes de Reacción abajo) pero
varían en títulos, KPIs precargados y textos de planes de reacción.
"""
from .models import (
    ProhibitionCatalog,
    RiskCatalog,
    Workstation,
    WorkstationBlock,
)


# ─────────────────────────────────────────────────────────────────────
# Configuración por rol (la "personalidad" de cada estación)
# ─────────────────────────────────────────────────────────────────────

ROLE_CONFIG = {
    Workstation.ROLE_PICKING: {
        'triggers_title': 'Disparadores Picking',
        'sic_title':      'SIC Picking',
        'plans_title':    'Planes de Reacción · Picking',
        'plans_kpi_label': 'Pallets / Hora',
        'yellow_desc':    'Revisar técnica de armado · pedir refuerzo si tarda > meta',
        'red_desc':       '5 Porqué + escalar a supervisor de bodega',
        # Filtro de codes para precarga (substrings que matchean nombres usuales).
        # Si ningún code matchea, cae a "primeros N de la lista".
        'metric_hints':   ['picker', 'picking', 'pallet', 'cajas_hora'],
    },
    Workstation.ROLE_PICKER: {
        'triggers_title': 'Disparadores Picker',
        'sic_title':      'SIC · Picker',
        'plans_title':    'Planes de Reacción · Picker',
        'plans_kpi_label': 'Pallets / Hora',
        'yellow_desc':    'Revisar técnica de armado · pedir refuerzo si tarda > meta',
        'red_desc':       '5 Porqué + escalar a supervisor de bodega',
        'metric_hints':   ['picker', 'pallet', 'pallets_hr', 'tiempo_pauta'],
    },
    Workstation.ROLE_COUNTER: {
        'triggers_title': 'Disparadores Conteo',
        'sic_title':      'SIC · Conteo',
        'plans_title':    'Planes de Reacción · Conteo',
        'plans_kpi_label': 'Tiempo de Conteo por Camión',
        'yellow_desc':    'Verificar tarima por tarima · documentar inconsistencia',
        'red_desc':       'Detener despacho · escalar a supervisor de operaciones',
        'metric_hints':   ['count', 'conteo', 'errores_conteo', 'pallets_contados', 'precision'],
    },
    Workstation.ROLE_YARD: {
        'triggers_title': 'Disparadores Patio',
        'sic_title':      'SIC · Chofer de Patio',
        'plans_title':    'Planes de Reacción · Patio',
        'plans_kpi_label': 'Tiempo Bahía → Estacionamiento',
        'yellow_desc':    'Confirmar bahía libre · revisar congestión en patio',
        'red_desc':       'Comunicar a torre de control · liberar bahía manualmente',
        'metric_hints':   ['yard', 'patio', 'bahia', 'estacionamiento', 'movimiento'],
    },
}


# ─────────────────────────────────────────────────────────────────────
# Builder genérico — usa ROLE_CONFIG según el rol
# ─────────────────────────────────────────────────────────────────────

def _select_metrics(all_codes: list[str], hints: list[str], take: int) -> list[str]:
    """Selecciona codes que matcheen los hints (substring case-insensitive).
    Si no matchea nada, devuelve los primeros `take` para que el bloque no
    quede vacío."""
    if not all_codes:
        return []
    lowered_hints = [h.lower() for h in hints]
    matches = [c for c in all_codes if any(h in c.lower() for h in lowered_hints)]
    if matches:
        return matches[:take]
    return all_codes[:take]


def _build_template(
    role: str,
    risk_ids: list[int],
    prohib_ids: list[int],
    all_metric_codes: list[str],
) -> list[dict]:
    cfg = ROLE_CONFIG.get(role) or ROLE_CONFIG[Workstation.ROLE_PICKER]
    triggers_codes = _select_metrics(all_metric_codes, cfg['metric_hints'], take=5)
    sic_codes = _select_metrics(all_metric_codes, cfg['metric_hints'], take=3)

    return [
        # ── Fila superior: Riesgos / Prohibiciones / Disparadores ──
        {
            'type': WorkstationBlock.TYPE_RISKS,
            'config': {'title': 'Riesgos del área', 'catalog_ids': risk_ids},
            'grid_x': 0, 'grid_y': 0, 'grid_w': 4, 'grid_h': 4,
        },
        {
            'type': WorkstationBlock.TYPE_PROHIBITIONS,
            'config': {'title': 'Prohibiciones del área', 'catalog_ids': prohib_ids},
            'grid_x': 4, 'grid_y': 0, 'grid_w': 4, 'grid_h': 4,
        },
        {
            'type': WorkstationBlock.TYPE_TRIGGERS,
            'config': {
                'title': cfg['triggers_title'],
                'metric_codes': triggers_codes,
                'items': [],
            },
            'grid_x': 8, 'grid_y': 0, 'grid_w': 4, 'grid_h': 4,
        },
        # ── Fila inferior: SIC + Planes de Reacción ──
        {
            'type': WorkstationBlock.TYPE_SIC_CHART,
            'config': {
                'title': cfg['sic_title'],
                'metric_codes': sic_codes,
                'cycle_seconds': 30,
                'kpis': [],
            },
            'grid_x': 0, 'grid_y': 4, 'grid_w': 8, 'grid_h': 8,
        },
        {
            'type': WorkstationBlock.TYPE_REACTION_PLANS,
            'config': {
                'title': cfg['plans_title'],
                'kpi_label': cfg['plans_kpi_label'],
                'yellow': {
                    'title': 'ZONA AMARILLA · Alerta',
                    'description': cfg['yellow_desc'],
                },
                'red': {
                    'title': 'ZONA ROJA · Crítica',
                    'description': cfg['red_desc'],
                },
            },
            'grid_x': 8, 'grid_y': 4, 'grid_w': 4, 'grid_h': 8,
        },
    ]


def _available_metric_codes_for_dc(dc_id: int) -> list[str]:
    """KPI Targets vigentes del CD → lista de codes únicos (orden estable).
    Devuelve [] si el CD no tiene targets o si la query falla."""
    try:
        from datetime import date as _date
        from django.db.models import Q
        from apps.truck_cycle.models.catalogs import KPITargetModel
        today = _date.today()
        qs = (
            KPITargetModel.objects
            .filter(
                distributor_center_id=dc_id,
                metric_type__isnull=False,
                metric_type__is_active=True,
                effective_from__lte=today,
            )
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
            .select_related('metric_type')
            .order_by('metric_type__name')
        )
        seen, out = set(), []
        for kpi in qs:
            code = kpi.metric_type.code
            if code in seen:
                continue
            seen.add(code)
            out.append(code)
        return out
    except Exception:
        return []


def apply_default_template(ws: Workstation) -> None:
    """Crea los bloques default de la estación según su rol.

    Cada rol arranca con:
      - Riesgos y Prohibiciones del catálogo master.
      - Disparadores y SIC precargados con los KPIs vigentes del CD que
        matcheen el rol (ej. picker → pallets/hr, counter → conteo).
      - Plan de Reacción con texto específico al rol.

    Idempotente al nivel de "siempre crea desde cero" — el caller debe
    limpiar bloques previos antes de re-aplicar.
    """
    risk_ids = list(RiskCatalog.objects.filter(is_active=True).values_list('id', flat=True))
    prohib_ids = list(ProhibitionCatalog.objects.filter(is_active=True).values_list('id', flat=True))
    metric_codes = _available_metric_codes_for_dc(ws.distributor_center_id)

    blocks_data = _build_template(ws.role, risk_ids, prohib_ids, metric_codes)
    bulk = [
        WorkstationBlock(
            workstation=ws,
            type=b['type'],
            config=b.get('config', {}),
            grid_x=b['grid_x'], grid_y=b['grid_y'],
            grid_w=b['grid_w'], grid_h=b['grid_h'],
            is_active=True,
        )
        for b in blocks_data
    ]
    WorkstationBlock.objects.bulk_create(bulk)
