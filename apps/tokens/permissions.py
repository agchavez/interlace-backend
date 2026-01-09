"""
Permisos personalizados para el módulo de tokens
"""
from rest_framework import permissions
from apps.personnel.models import PersonnelProfile


class CanRequestTokens(permissions.BasePermission):
    """
    Permiso para crear solicitudes de tokens.
    Solo supervisores y superiores con acceso al sistema pueden solicitar.
    """
    message = "Solo supervisores y superiores pueden solicitar tokens."

    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            personnel = request.user.personnel_profile
            return personnel.can_request_tokens()
        except (PersonnelProfile.DoesNotExist, AttributeError):
            return False


class CanApproveTokenL1(permissions.BasePermission):
    """
    Permiso para aprobar tokens de nivel 1.
    Supervisores, Jefes de Área y Gerentes de CD.
    """
    message = "No tiene permiso para aprobar tokens de nivel 1."

    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            personnel = request.user.personnel_profile
            return personnel.can_approve_tokens_level_1()
        except (PersonnelProfile.DoesNotExist, AttributeError):
            return False


class CanApproveTokenL2(permissions.BasePermission):
    """
    Permiso para aprobar tokens de nivel 2.
    Jefes de Área y Gerentes de CD.
    """
    message = "No tiene permiso para aprobar tokens de nivel 2."

    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            personnel = request.user.personnel_profile
            return personnel.can_approve_tokens_level_2()
        except (PersonnelProfile.DoesNotExist, AttributeError):
            return False


class CanApproveTokenL3(permissions.BasePermission):
    """
    Permiso para aprobar tokens de nivel 3.
    Solo Gerentes de CD.
    """
    message = "No tiene permiso para aprobar tokens de nivel 3."

    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            personnel = request.user.personnel_profile
            return personnel.can_approve_tokens_level_3()
        except (PersonnelProfile.DoesNotExist, AttributeError):
            return False


class CanValidateToken(permissions.BasePermission):
    """
    Permiso para validar tokens (escaneo QR en portería).
    Solo personal de Seguridad.
    """
    message = "Solo el personal de Seguridad puede validar tokens."

    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            personnel = request.user.personnel_profile
            return personnel.can_validate_tokens()
        except (PersonnelProfile.DoesNotExist, AttributeError):
            return False


class IsTokenOwnerOrApprover(permissions.BasePermission):
    """
    Permiso para ver un token específico.
    - El beneficiario del token
    - El solicitante del token
    - Aprobadores del nivel actual o superior
    - Personal de Seguridad
    """
    message = "No tiene permiso para ver este token."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.is_staff:
            return True

        try:
            personnel = user.personnel_profile
        except (PersonnelProfile.DoesNotExist, AttributeError):
            return False

        # Es el beneficiario
        if obj.personnel == personnel:
            return True

        # Es el solicitante
        if obj.requested_by == user:
            return True

        # Es un aprobador
        if personnel.can_approve_tokens_level_1():
            return True

        # Es personal de Seguridad
        if personnel.can_validate_tokens():
            return True

        return False
