from rest_framework.exceptions import APIException, status

class TrailerRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El trailer es obligatorio',
        'error_code': 'required_trailer'
    }
    default_code = 'required_trailer'

class TransporterRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El transportista es obligatorio',
        'error_code': 'required_transporter'
    }
    default_code = 'required_transporter'


# No se puede actualizar un tracker completado
class TrackerCompleted(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No se puede actualizar un tracker completado',
        'error_code': 'tracker_completed'
    }
    default_code = 'tracker_completed'

# Se requiere un usuario con un centro de distribución asignado
class UserWithoutDistributorCenter(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El usuario no tiene un centro de distribución asignado',
        'error_code': 'user_without_distributor_center'
    }
    default_code = 'user_without_distributor_center'


# La suma de los pallets supera la establecida
class PalletsExceeded(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'La suma de los pallets supera la establecida',
        'error_code': 'pallets_exceeded'
    }
    default_code = 'pallets_exceeded'

