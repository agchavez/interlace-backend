from rest_framework.exceptions import APIException, status


class NoDistributionCenterError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El usuario no tiene centro de distribucion',
        'error_code': 'no_distribution_center'
    }
    default_code = 'no_distribution_center'

class NoPeriodError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No hay periodos en este centro de distribución',
        'error_code': 'no_period_found'
    }
    default_code = 'no_period_found'