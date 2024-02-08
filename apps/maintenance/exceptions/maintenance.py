from rest_framework.exceptions import APIException, status


class NoDistributionCenterError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El usuario no tiene centro de distribucion',
        'error_code': 'no_distribution_center'
    }
    default_code = 'no_distribution_center'

# EL CENMTRO DE DISTRIBUCION NO EXISTE
class DistributionCenterDoesNotExistError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El centro de distribucion no existe',
        'error_code': 'distribution_center_does_not_exist'
    }
    default_code = 'distribution_center_does_not_exist'
class NoPeriodError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No hay periodos en este centro de distribución',
        'error_code': 'no_period_found'
    }
    default_code = 'no_period_found'

class NoProductError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Debe proporcionar un id de producto',
        'error_code': 'product_not_provided'
    }
    default_code = 'product_not_provided'

class ProductNoIntegerError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El id del producto debe ser un número entero',
        'error_code': 'product_id_not_int'
    }
    default_code = 'product_id_not_int'

# No existe el producto en el centro de distribución
class ProductDoesNotExistError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El producto no existe en el centro de distribución',
        'error_code': 'product_does_not_exist'
    }
    default_code = 'product_does_not_exist'


# Ya existe el lote para el Centro de Distribución
class LotAlreadyExistsError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Ya existe un lote con el mismo codigo para el centro de distribución',
        'error_code': 'lot_already_exists'
    }
    default_code = 'lot_already_exists'

# El lote no es valido para este centro de distribución
class LotNotValidError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El lote no es valido para este centro de distribución',
        'error_code': 'lot_not_valid'
    }
    default_code = 'lot_not_valid'