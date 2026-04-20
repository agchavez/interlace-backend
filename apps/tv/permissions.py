from rest_framework import permissions


class HasTvSession(permissions.BasePermission):
    """Permite la request solo si la autenticación TvToken adjuntó una sesión."""
    message = 'Se requiere un token válido de TV.'

    def has_permission(self, request, view):
        return getattr(request, 'tv_session', None) is not None
