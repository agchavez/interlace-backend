from rest_framework.exceptions import APIException, status


class QuantityExceeded(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'La cantidad de productos supera la disponible',
        'error_code': 'quantity_exceeded'
    }
    default_code = 'quantity_exceeded'

