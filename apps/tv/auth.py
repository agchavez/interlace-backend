"""
Autenticación basada en TvToken.

El cliente (la TV) envía el token en el header `X-TV-Token`. Resolvemos a una
TvSession activa (PAIRED + no expirada) e inyectamos la sesión en el request
como `request.tv_session`. No creamos sesión de usuario — la TV no tiene user.
"""
from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import TvSession


class TvTokenAuthentication(authentication.BaseAuthentication):
    """
    Autentica por header `X-TV-Token`. El "usuario" resultante es anónimo pero
    `request.tv_session` queda disponible para scoping de datos.
    """
    keyword = 'X-TV-Token'

    def authenticate(self, request):
        token = request.META.get('HTTP_X_TV_TOKEN')
        if not token:
            return None

        try:
            session = TvSession.objects.select_related('distributor_center').get(access_token=token)
        except TvSession.DoesNotExist:
            raise exceptions.AuthenticationFailed('Token de TV inválido.')

        if session.status != 'PAIRED' or session.is_expired:
            raise exceptions.AuthenticationFailed('Sesión de TV expirada o revocada.')

        # Actualiza heartbeat sin bloquear el request.
        TvSession.objects.filter(pk=session.pk).update(last_seen_at=timezone.now())

        request.tv_session = session
        # DRF necesita devolver un "user". Usamos AnonymousUser + un atributo custom
        # en request (tv_session) — las views lo consultan para el scoping.
        from django.contrib.auth.models import AnonymousUser
        return (AnonymousUser(), session)

    def authenticate_header(self, request):
        return self.keyword
