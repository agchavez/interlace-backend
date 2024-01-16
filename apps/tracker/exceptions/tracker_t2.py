from rest_framework.exceptions import APIException, status

# la cantidad no puede superar a la cantidad de salida
class QuantityExceededOut(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'La cantidad de productos supera la disponible',
        'error_code': 'quantity_exceeded'
    }
    default_code = 'quantity_exceeded_out'

# cantidad mayor a 0
class QuantityMajorZero(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'La cantidad debe ser mayor a 0',
        'error_code': 'quantity_exceeded'
    }
    default_code = 'quantity_exceeded'

# ya existe un registro de salida de t2 con el mismo tracker_detail
class TrackerDetailExist(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Ya existe un registro de salida de t2 con el mismo tracker_detail',
        'error_code': 'tracker_detail_exist'
    }
    default_code = 'tracker_detail_exist'

# Cada elemento debe tener 'tracker_detail_product'.
class TrackerDetailProductRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Cada elemento debe tener tracker_detail_product',
        'error_code': 'tracker_detail_product_required'
    }
    default_code = 'tracker_detail_product_required'

#Cada elemento debe tener 'quantity'.
class QuantityRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Cada elemento debe tener quantity',
        'error_code': 'quantity_required'
    }
    default_code = 'quantity_required'


#La suma de las cantidades no puede ser mayor a la cantidad de la salida.
class QuantitySumExceeded(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'La suma de las cantidades no puede ser mayor a la cantidad de la salida',
        'error_code': 'quantity_sum_exceeded'
    }
    default_code = 'quantity_sum_exceeded'


# Solo se puede eliminar el registros con estado de creado
class DeleteStateCreated(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': "No se puede eliminar el registros con estado de Completado",
        'error_code': 'delete_state_created'
    }
    default_code = 'delete_state_created'

# Nop se puede eliminar el registro si tiene