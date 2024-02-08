from rest_framework.exceptions import APIException, status


class TrailerRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El trailer es obligatorio',
        'error_code': 'required_trailer'
    }
    default_code = 'required_trailer'


# Se requiere un movitivo para el movimiento de inventario
class ReasonRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El motivo es obligatorio',
        'error_code': 'required_reason'
    }
    default_code = 'required_reason'

# Se requiere un archivo de excel para el movimiento de inventario
class FileRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El archivo es obligatorio',
        'error_code': 'required_file'
    }
    default_code = 'required_file'

# El archivo de excel debe tener las columnas requeridas
class RequiredColumns(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El archivo debe tener las columnas requeridas',
        'error_code': 'required_columns'
    }
    default_code = 'required_columns'

# Archivo no valido
class InvalidFile(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El archivo no es valido',
        'error_code': 'invalid_file'
    }
    default_code = 'invalid_file'
