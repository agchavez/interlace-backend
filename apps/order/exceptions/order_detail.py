from rest_framework.exceptions import APIException, status


class QuantityExceeded(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'La cantidad de productos supera la disponible',
        'error_code': 'quantity_exceeded'
    }
    default_code = 'quantity_exceeded'

# Ya existe un registro con la orden y el detalle de tracker
class OrderDetailExist(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Ya existe un registro con la orden y el detalle de tracker',
        'error_code': 'order_detail_exist'
    }
    default_code = 'order_detail_exist'

