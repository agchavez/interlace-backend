from rest_framework.exceptions import APIException, status

class RegisterLogNotFoundException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Se produjo un error para el evento log.'
    default_code = 4524