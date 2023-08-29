# custom handler
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, APIException):
        if response is not None:
            params = exc.get_full_details()
            response.data['status_code'] = response.status_code
            if 'code' in params:
                response.data['error_code'] = params['code']
            else:
                try:
                    response.data['error_code'] = get_error_code(response.data['detail'])
                except :
                    pass
    return response


def get_error_code(detail):
    if detail == 'Las credenciales de autenticación no se proveyeron.':
        return 4499
    else:
        return 'Error no registrado'