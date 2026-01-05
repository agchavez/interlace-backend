"""
Permisos personalizados para el módulo de personal
"""
from rest_framework import permissions
from .models.personnel import PersonnelProfile


class IsPersonnelOwner(permissions.BasePermission):
    """
    Permiso: El usuario puede acceder a su propio perfil
    """
    def has_object_permission(self, request, view, obj):
        # Verificar si el objeto tiene relación con personnel
        if isinstance(obj, PersonnelProfile):
            return obj.user == request.user
        return False


class IsSupervisorOrAbove(permissions.BasePermission):
    """
    Permiso: El usuario es supervisor o superior, o staff/superuser
    """
    def has_permission(self, request, view):
        # Superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            personnel = request.user.personnel_profile
            # Permitir a RRHH/People
            if personnel.area.code == 'PEOPLE':
                return True
            return personnel.can_approve_tokens_level_1()
        except PersonnelProfile.DoesNotExist:
            return False


class IsAreaManagerOrAbove(permissions.BasePermission):
    """
    Permiso: El usuario es jefe de área o superior
    """
    def has_permission(self, request, view):
        try:
            personnel = request.user.personnel_profile
            return personnel.can_approve_tokens_level_2()
        except PersonnelProfile.DoesNotExist:
            return False


class IsCDManager(permissions.BasePermission):
    """
    Permiso: El usuario es gerente de centro de distribución
    """
    def has_permission(self, request, view):
        try:
            personnel = request.user.personnel_profile
            return personnel.can_approve_tokens_level_3()
        except PersonnelProfile.DoesNotExist:
            return False


class CanViewPersonnel(permissions.BasePermission):
    """
    Permiso: Puede ver personal
    - Superusuarios y staff pueden ver todo
    - Usuarios con permiso view_all_personnel
    - Propio perfil siempre
    - Su equipo si es supervisor
    - Su área si es jefe de área
    - Todo el CD si es gerente
    """
    def has_permission(self, request, view):
        # Superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuarios con permisos de Django
        if request.user.has_perm('personnel.view_all_personnel'):
            return True

        return True  # Permitir el acceso, luego validar en has_object_permission

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, PersonnelProfile):
            return False

        # Superusuarios y staff pueden ver todo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Usuarios con permiso pueden ver todo
        if request.user.has_perm('personnel.view_all_personnel'):
            return True

        try:
            user_personnel = request.user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return False

        # Propio perfil
        if obj == user_personnel:
            return True

        # Gerente CD puede ver todo su centro
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return obj.primary_distributor_center == user_personnel.primary_distributor_center

        # Jefe de área puede ver su área
        if user_personnel.hierarchy_level == PersonnelProfile.AREA_MANAGER:
            return obj.area == user_personnel.area

        # Supervisor puede ver su equipo
        if user_personnel.hierarchy_level == PersonnelProfile.SUPERVISOR:
            subordinates = user_personnel.get_all_subordinates()
            return obj in subordinates or obj.immediate_supervisor == user_personnel

        return False


class CanViewMedicalRecords(permissions.BasePermission):
    """
    Permiso: Puede ver registros médicos
    - People/RRHH siempre
    - Gerente CD de mismo centro
    - Propio registro siempre
    """
    def has_object_permission(self, request, view, obj):
        try:
            user_personnel = request.user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return False

        # Propio registro
        if obj.personnel == user_personnel:
            return True

        # Área de People/RRHH
        if user_personnel.area.code == 'PEOPLE':
            return True

        # Gerente CD del mismo centro
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return obj.personnel.primary_distributor_center == user_personnel.primary_distributor_center

        return False


class CanManagePersonnel(permissions.BasePermission):
    """
    Permiso: Puede crear/editar personal
    - Superusuarios (is_superuser o is_staff)
    - Usuarios con permisos de Django (manage_personnel)
    - People/RRHH
    - Gerente CD
    - Jefe de área (solo su área)
    """
    def has_permission(self, request, view):
        # Superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permisos de Django
        if request.user.has_perm('personnel.manage_personnel'):
            return True

        try:
            personnel = request.user.personnel_profile
            return (
                personnel.area.code == 'PEOPLE' or
                personnel.hierarchy_level in [
                    PersonnelProfile.CD_MANAGER,
                    PersonnelProfile.AREA_MANAGER
                ]
            )
        except PersonnelProfile.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # Superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True

        try:
            user_personnel = request.user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return False

        # People/RRHH puede gestionar todo
        if user_personnel.area.code == 'PEOPLE':
            return True

        # Gerente CD puede gestionar su centro
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return obj.primary_distributor_center == user_personnel.primary_distributor_center

        # Jefe de área puede gestionar su área
        if user_personnel.hierarchy_level == PersonnelProfile.AREA_MANAGER:
            return obj.area == user_personnel.area

        return False
