from rest_framework import permissions


class HasTvSession(permissions.BasePermission):
    """Permite la request solo si la autenticación TvToken adjuntó una sesión."""
    message = 'Se requiere un token válido de TV.'

    def has_permission(self, request, view):
        return getattr(request, 'tv_session', None) is not None


class IsAuthenticatedOrTv(permissions.BasePermission):
    """JWT user autenticado O TV con sesión válida.

    Para endpoints que las TVs necesitan leer (catálogos read-only, métricas
    agregadas) sin tener un usuario humano detrás. La TV no puede mutar — se
    combina con `IsAdmin` o similar para gatear escrituras al user humano.
    """
    message = 'Autenticación requerida (usuario o TV).'

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return getattr(request, 'tv_session', None) is not None
