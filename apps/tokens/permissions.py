"""
Permisos personalizados para el módulo de tokens.

Sistema Híbrido:
- Permisos Django (auth_permission) → Control de acceso a funciones
- Jerarquía (hierarchy_level) → Validaciones de nivel de aprobación
- Área (area.code) → Funciones especiales (Seguridad)
- Centro de distribución → Filtrado de datos
"""
from rest_framework import permissions
from apps.personnel.models import PersonnelProfile


class HasTokenPermission(permissions.BasePermission):
    """
    Clase base para verificar permisos de Django del módulo tokens.
    Las subclases deben definir `permission_codename`.

    Si el permiso no existe aún en la BD, permite acceso basado en jerarquía
    como fallback para compatibilidad durante la migración.
    """
    permission_codename = None
    message = "No tiene permiso para realizar esta acción."
    fallback_hierarchy_levels = None  # Lista de niveles permitidos como fallback

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        # Verificar permiso de Django
        if self.permission_codename:
            perm_string = f'tokens.{self.permission_codename}'
            if request.user.has_perm(perm_string):
                return True

        # Fallback a jerarquía si está definido
        if self.fallback_hierarchy_levels:
            try:
                personnel = request.user.personnel_profile
                if personnel.hierarchy_level in self.fallback_hierarchy_levels:
                    return True
            except (PersonnelProfile.DoesNotExist, AttributeError):
                pass

        return False


class CanRequestTokens(HasTokenPermission):
    """
    Permiso para crear solicitudes de tokens.
    - Permiso Django: tokens.add_tokenrequest
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'add_tokenrequest'
    fallback_hierarchy_levels = [
        PersonnelProfile.SUPERVISOR,
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para crear tokens."


class CanApproveTokenL1(HasTokenPermission):
    """
    Permiso para aprobar tokens de nivel 1.
    - Permiso Django: tokens.can_approve_level_1
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'can_approve_level_1'
    fallback_hierarchy_levels = [
        PersonnelProfile.SUPERVISOR,
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para aprobar tokens de nivel 1."


class CanApproveTokenL2(HasTokenPermission):
    """
    Permiso para aprobar tokens de nivel 2.
    - Permiso Django: tokens.can_approve_level_2
    - Fallback: AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'can_approve_level_2'
    fallback_hierarchy_levels = [
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para aprobar tokens de nivel 2."


class CanApproveTokenL3(HasTokenPermission):
    """
    Permiso para aprobar tokens de nivel 3.
    - Permiso Django: tokens.can_approve_level_3
    - Fallback: CD_MANAGER
    """
    permission_codename = 'can_approve_level_3'
    fallback_hierarchy_levels = [
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para aprobar tokens de nivel 3."


class CanValidateToken(permissions.BasePermission):
    """
    Permiso para validar tokens (escaneo QR en portería).
    - Permiso Django: tokens.can_validate_token
    - Fallback: Área SECURITY o CD_MANAGER
    """
    message = "No tiene permiso para validar tokens."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        # Verificar permiso de Django
        if request.user.has_perm('tokens.can_validate_token'):
            return True

        # Fallback: Área de Seguridad o Gerente CD
        try:
            personnel = request.user.personnel_profile

            # Personal de Seguridad
            if personnel.area and personnel.area.code == 'SECURITY':
                return True

            # Gerente de CD (para emergencias)
            if personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
                return True
        except (PersonnelProfile.DoesNotExist, AttributeError):
            pass

        return False


class CanDownloadPdf(HasTokenPermission):
    """
    Permiso para descargar PDF de tokens.
    - Permiso Django: tokens.can_download_pdf
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'can_download_pdf'
    fallback_hierarchy_levels = [
        PersonnelProfile.SUPERVISOR,
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para descargar PDF de tokens."


class CanDownloadReceipt(HasTokenPermission):
    """
    Permiso para descargar recibos de tokens.
    - Permiso Django: tokens.can_download_receipt
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER, SECURITY
    """
    permission_codename = 'can_download_receipt'
    message = "No tiene permiso para descargar recibos de tokens."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.user.has_perm('tokens.can_download_receipt'):
            return True

        # Fallback
        try:
            personnel = request.user.personnel_profile

            # Jerarquía supervisor+
            if personnel.hierarchy_level in [
                PersonnelProfile.SUPERVISOR,
                PersonnelProfile.AREA_MANAGER,
                PersonnelProfile.CD_MANAGER,
            ]:
                return True

            # Personal de Seguridad
            if personnel.area and personnel.area.code == 'SECURITY':
                return True
        except (PersonnelProfile.DoesNotExist, AttributeError):
            pass

        return False


class CanCompleteDelivery(HasTokenPermission):
    """
    Permiso para completar entrega de uniformes.
    - Permiso Django: tokens.can_complete_delivery
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'can_complete_delivery'
    fallback_hierarchy_levels = [
        PersonnelProfile.SUPERVISOR,
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para completar entregas de uniformes."


class CanRejectToken(HasTokenPermission):
    """
    Permiso para rechazar tokens.
    - Permiso Django: tokens.can_reject_token
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'can_reject_token'
    fallback_hierarchy_levels = [
        PersonnelProfile.SUPERVISOR,
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para rechazar tokens."


class CanCancelToken(HasTokenPermission):
    """
    Permiso para cancelar tokens.
    - Permiso Django: tokens.can_cancel_token
    - Fallback: SUPERVISOR, AREA_MANAGER, CD_MANAGER
    """
    permission_codename = 'can_cancel_token'
    fallback_hierarchy_levels = [
        PersonnelProfile.SUPERVISOR,
        PersonnelProfile.AREA_MANAGER,
        PersonnelProfile.CD_MANAGER,
    ]
    message = "No tiene permiso para cancelar tokens."


class IsTokenOwnerOrApprover(permissions.BasePermission):
    """
    Permiso para ver un token específico.
    Combina permisos y jerarquía:
    - El beneficiario del token (siempre puede ver su token)
    - El solicitante del token
    - Usuarios con permiso view_tokenrequest
    - Usuarios con jerarquía SUPERVISOR+ (fallback)
    """
    message = "No tiene permiso para ver este token."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True

        # Tiene permiso general de ver tokens
        if user.has_perm('tokens.view_tokenrequest'):
            return True

        try:
            personnel = user.personnel_profile
        except (PersonnelProfile.DoesNotExist, AttributeError):
            personnel = None

        # Es el beneficiario
        if personnel and obj.personnel == personnel:
            return True

        # Es el solicitante
        if obj.requested_by == user:
            return True

        # Fallback: tiene jerarquía supervisor+
        if personnel and personnel.hierarchy_level in [
            PersonnelProfile.SUPERVISOR,
            PersonnelProfile.AREA_MANAGER,
            PersonnelProfile.CD_MANAGER,
        ]:
            return True

        # Fallback: es personal de Seguridad
        if personnel and personnel.area and personnel.area.code == 'SECURITY':
            return True

        return False
