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

# no se puede actualizar una orden que no esta en estado COMPLETED o IN_PROCESS
class OrderNotCompleted(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No se puede actualizar una orden que no esta en estado Completado o En proceso',
        'error_code': 'order_not_completed'
    }
    default_code = 'order_not_completed'

class CustomAPIException(APIException):
    def __init__(self, detail, code, status_code=status.HTTP_400_BAD_REQUEST):
        self.status_code = status_code
        self.default_detail = {
            'mensage': detail,
            'error_code': code
        }
        self.default_code = code
        super().__init__(detail, code)