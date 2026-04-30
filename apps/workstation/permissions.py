"""
Permisos del módulo Workstation.

Solo admin (staff/superuser) o jefe (CD_MANAGER) del CD asociado al workstation
pueden crear/editar/eliminar config. Lectura abierta a cualquier usuario auth.
"""
from rest_framework import permissions

from apps.personnel.models.personnel import PersonnelProfile

from .models import Workstation


def _is_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def _is_cd_chief_for(user, distributor_center_id: int | None) -> bool:
    """True si el user es CD_MANAGER del CD indicado."""
    if not (user and user.is_authenticated and distributor_center_id):
        return False
    try:
        personnel = user.personnel_profile
    except PersonnelProfile.DoesNotExist:
        return False
    if personnel.hierarchy_level != PersonnelProfile.CD_MANAGER:
        return False
    return personnel.distributor_centers.filter(pk=distributor_center_id).exists()


def _resolve_dc_id(obj) -> int | None:
    """Devuelve el id del CD asociado al objeto (sea Workstation o sub-recurso)."""
    if isinstance(obj, Workstation):
        return obj.distributor_center_id
    ws = getattr(obj, 'workstation', None)
    if ws is not None:
        return ws.distributor_center_id
    return None


class IsAdminOrCDChief(permissions.BasePermission):
    """
    Lectura: cualquier autenticado.
    Escritura (POST/PUT/PATCH/DELETE): admin o jefe del CD del workstation.

    Para create se valida en `has_permission` con el CD enviado en el payload
    (`distributor_center` o, si es sub-recurso, vía el workstation referenciado).
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True

        # Para create, mirar el CD del payload.
        if view.action == 'create':
            dc_id = request.data.get('distributor_center')
            if dc_id is None:
                ws_id = request.data.get('workstation')
                if ws_id:
                    ws = Workstation.objects.filter(pk=ws_id).only('distributor_center_id').first()
                    dc_id = ws.distributor_center_id if ws else None
            try:
                dc_id = int(dc_id) if dc_id is not None else None
            except (TypeError, ValueError):
                dc_id = None
            return _is_cd_chief_for(request.user, dc_id)

        return True  # update/delete validan en has_object_permission

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True
        return _is_cd_chief_for(request.user, _resolve_dc_id(obj))


class IsAdmin(permissions.BasePermission):
    """Solo admin (staff/superuser) — usado para los catálogos master."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return _is_admin(request.user)
