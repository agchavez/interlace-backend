"""Semaforización de métricas según KPITargetModel (Meta / Disparador / Dirección).

Bandas:
- GREEN  → el valor cumple la Meta.
- YELLOW → el valor pasó la Meta pero aún no cruzó el Disparador.
- RED    → el valor cruzó el Disparador.
- GRAY   → no hay valor o no hay target configurado.
"""
from datetime import date
from typing import Optional

from django.db.models import Q

BAND_GREEN = 'GREEN'
BAND_YELLOW = 'YELLOW'
BAND_RED = 'RED'
BAND_GRAY = 'GRAY'

DIRECTION_HIGHER = 'HIGHER_IS_BETTER'
DIRECTION_LOWER = 'LOWER_IS_BETTER'


def compute_band(value, target, trigger, direction: str) -> str:
    """Clasifica un valor en una banda según meta/disparador/dirección.

    Si `trigger` es None, se comporta como un umbral único (verde/rojo).
    """
    if value is None or target is None:
        return BAND_GRAY

    v = float(value)
    t = float(target)
    w = float(trigger) if trigger is not None else None

    if direction == DIRECTION_HIGHER:
        if v >= t:
            return BAND_GREEN
        if w is None:
            return BAND_RED
        return BAND_YELLOW if v >= w else BAND_RED

    # LOWER_IS_BETTER
    if v <= t:
        return BAND_GREEN
    if w is None:
        return BAND_RED
    return BAND_YELLOW if v <= w else BAND_RED


def get_kpi_target(metric_type_id: int, distributor_center_id: Optional[int], on_date: Optional[date] = None):
    """Devuelve el KPITarget vigente para (metric_type, dc) en una fecha."""
    from apps.truck_cycle.models.catalogs import KPITargetModel

    on_date = on_date or date.today()
    qs = (
        KPITargetModel.objects
        .filter(metric_type_id=metric_type_id, effective_from__lte=on_date)
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=on_date))
    )

    if distributor_center_id is not None:
        dc_target = qs.filter(distributor_center_id=distributor_center_id).order_by('-effective_from').first()
        if dc_target:
            return dc_target

    return None


def band_for(value, metric_type_id: int, distributor_center_id: Optional[int], on_date: Optional[date] = None) -> dict:
    """Dict listo para el response: value + target + trigger + direction + unit + band."""
    target_obj = get_kpi_target(metric_type_id, distributor_center_id, on_date)
    if not target_obj:
        return {
            'value': None if value is None else float(value),
            'target': None,
            'trigger': None,
            'direction': None,
            'unit': None,
            'band': BAND_GRAY,
        }

    band = compute_band(value, target_obj.target_value, target_obj.warning_threshold, target_obj.direction)
    return {
        'value': None if value is None else float(value),
        'target': float(target_obj.target_value),
        'trigger': float(target_obj.warning_threshold) if target_obj.warning_threshold is not None else None,
        'direction': target_obj.direction,
        'unit': target_obj.unit or (target_obj.metric_type.unit if target_obj.metric_type else ''),
        'band': band,
    }
