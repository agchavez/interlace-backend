from rest_framework import serializers
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    raise serializers.ValidationError("El usuario está desactivado.")

                return user
            else:
                raise serializers.ValidationError("Credenciales inválidas. Por favor, inténtelo de nuevo.")

        else:
            raise serializers.ValidationError("Debe ingresar email y contraseña.")