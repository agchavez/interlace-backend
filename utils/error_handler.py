# custom handler
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    try:

        if isinstance(exc, APIException):
            if response is not None:
                params = exc.get_full_details()
                # si data es una lista de errores
                response.data['status_code'] = response.status_code
                if 'code' in params:
                    response.data['error_code'] = params['code']
                    if params['code'] == 'token_not_valid':
                        response.data['mensage'] = 'El token de autenticación no es válido'
                        response.data['detail'] = 'El token de autenticación no es válido'
                        return response
                if 'error_code' in params:
                    try:
                        response.data['error_code'] = get_error_code(response.data['detail'])
                        response.data['mensage'] = response.data['detail']
                    except :
                        pass
                else:
                    try:
                        response.data['error_code'] = params['code']
                        response.data['mensage'] = params['message']
                    except:
                        pass
                # Los demas errores que tienen sus propias llaves se agregan al arreglo de errores menos error_code
                if 401 == response.status_code:
                    response.data['mensage'] = 'No autorizado'
                    response.data['detail'] = 'No autorizado'
                else:
                    response.data['detail'] = params
                    if isinstance(response.data['detail'], dict):
                        response.data['detail'].pop('code', None)
                        response.data['detail'].pop('error_code', None)
                        response.data['detail'].pop('status_code', None)
            return response
    except:
        return response


def get_error_code(detail):
    if detail == 'Las credenciales de autenticación no se proveyeron.':
        return 4499
    else:
        return 'Error no registrado'