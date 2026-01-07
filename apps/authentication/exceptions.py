"""
Excepciones personalizadas para el módulo de autenticación
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidCredentials(APIException):
    """Excepción cuando las credenciales son inválidas"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Credenciales inválidas. Por favor, inténtelo de nuevo.',
        'error_code': 'invalid_credentials'
    }
    default_code = 'invalid_credentials'


class UserInactive(APIException):
    """Excepción cuando el usuario está desactivado"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {
        'mensage': 'El usuario está desactivado. Contacte al administrador.',
        'error_code': 'user_inactive'
    }
    default_code = 'user_inactive'


class MissingCredentials(APIException):
    """Excepción cuando faltan credenciales"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Debe ingresar email y contraseña.',
        'error_code': 'missing_credentials'
    }
    default_code = 'missing_credentials'


class EmailAlreadyExists(APIException):
    """Excepción cuando el email ya está registrado"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El email ya está registrado.',
        'error_code': 'email_already_exists'
    }
    default_code = 'email_already_exists'


class UsernameAlreadyExists(APIException):
    """Excepción cuando el username ya existe"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El nombre de usuario ya existe.',
        'error_code': 'username_already_exists'
    }
    default_code = 'username_already_exists'


class TokenExpired(APIException):
    """Excepción cuando el token ha expirado"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {
        'mensage': 'El token ha expirado. Por favor, inicie sesión nuevamente.',
        'error_code': 'token_expired'
    }
    default_code = 'token_expired'


class TokenInvalid(APIException):
    """Excepción cuando el token es inválido"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {
        'mensage': 'Token inválido.',
        'error_code': 'token_invalid'
    }
    default_code = 'token_invalid'
