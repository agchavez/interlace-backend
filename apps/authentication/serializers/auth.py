from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from ..exceptions import InvalidCredentials, UserInactive, MissingCredentials
import re

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(
        required=True,
        help_text='Puede ser correo electrónico o nombre de usuario'
    )
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        login = data.get('login')
        password = data.get('password')

        if not login or not password:
            raise MissingCredentials()

        # Determinar si es email o username
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email = re.match(email_pattern, login)

        user = None

        if is_email:
            # Intentar autenticar con email
            user = authenticate(email=login, password=password)
        else:
            # Intentar autenticar con username
            # Primero buscamos el usuario por username y obtenemos su email
            try:
                user_obj = User.objects.get(username=login)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                pass

        if user:
            if not user.is_active:
                raise UserInactive()
            return user
        else:
            raise InvalidCredentials()

    # Mantener retrocompatibilidad con el campo 'email'
    email = serializers.EmailField(required=False, write_only=True)

    def to_internal_value(self, data):
        # Si viene 'email', lo mapeamos a 'login'
        if 'email' in data and 'login' not in data:
            data['login'] = data['email']
        return super().to_internal_value(data)