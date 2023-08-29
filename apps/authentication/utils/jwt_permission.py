import jwt
from django.conf import settings

from django.contrib.auth import get_user_model
User = get_user_model()


from rest_framework import authentication, exceptions
from functools import wraps
from django.http import HttpResponseForbidden


class JWTAuth(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request)
        if not auth_header:
            return None

        try:
            token = auth_header.decode('utf-8').split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['id']
            user_email = payload['email']
            user = User.objects.get(id=user_id, email=user_email)
            return (user, token)

        except jwt.exceptions.DecodeError:
            raise exceptions.AuthenticationFailed('Invalid token.')

        except jwt.exceptions.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired.')

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user.')


def jwt_permission_required(permissions):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Verificar si el token es válido y obtener el usuario autenticado
            auth = JWTAuth()
            user = auth.authenticate(request)

            # permisos de usuario
            print(user[0].get_all_permissions())
            if user is not None and all([user[0].has_perm(perm) for perm in permissions]):
                # Si el usuario tiene los permisos requeridos, permitir el acceso a la vista
                return view_func(request, *args, **kwargs)
            else:
                # Si el usuario no tiene los permisos requeridos, denegar el acceso a la vista
                return HttpResponseForbidden()

        return wrapped_view

    return decorator
