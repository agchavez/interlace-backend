"""General web socket middlewares
"""

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication

from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.db import close_old_connections
from urllib.parse import parse_qs
from jwt import decode as jwt_decode
from django.conf import settings

from apps.user.models import UserModel


@database_sync_to_async
def get_user(validated_token):
    try:
        user = get_user_model().objects.get(id=validated_token["user_id"])
        # return get_user_model().objects.get(id=toke_id)
        print(f"{user}")
        return user

    except UserModel.DoesNotExist:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        path = scope.get('path', '?')
        qs_raw = scope["query_string"].decode("utf8")
        qs = parse_qs(qs_raw)
        print(f'[JwtAuth] path={path} qs_keys={list(qs.keys())} qs_raw_len={len(qs_raw)}')

        if "token" not in qs:
            return await self.inner(scope, receive, send)
        token = qs["token"][0]
        try:
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            print(f'[JwtAuth] token inválido para {path}: {e}')
            return None
        else:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope["user"] = await get_user(validated_token=decoded_data)
            print(f'[JwtAuth] user seteado en scope para {path}: {scope["user"]!r}')
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    # Orden importa: AuthMiddlewareStack corre primero (setea AnonymousUser por
    # default si no hay sesión Django), y luego JwtAuthMiddleware sobreescribe
    # `scope["user"]` con el user del JWT cuando viene `?token=` en el query.
    # Si invertimos, AuthMiddlewareStack pisa el user que el JWT ya seteó
    # y el consumer ve AnonymousUser → cierra el WebSocket con REJECT.
    return AuthMiddlewareStack(JwtAuthMiddleware(inner))