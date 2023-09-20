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


# No se puede registrar un tracker con un trailer que ya este en uso (PENDING)
class TrailerInUse(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No se puede registrar un seguimiento con un trailer que este aun en revisión',
        'error_code': 'trailer_in_use'
    }
    default_code = 'trailer_in_use'


# nose puede agregar o actualizar un detalle de tracker si el tracker ya esta completado
class TrackerCompletedDetail(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No se puede agregar o actualizar un detalle de tracker si el tracker ya esta completado',
        'error_code': 'tracker_completed_detail'
    }
    default_code = 'tracker_completed_detail'


# nose puede agregar o actualizar un detalle de producto si el tracker ya esta completado
class TrackerCompletedDetailProduct(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'No se puede agregar o actualizar un detalle de producto si el tracker ya esta completado',
        'error_code': 'tracker_completed_detail_product'
    }
    default_code = 'tracker_completed_detail_product'


class InputDocumentNumberRegistered(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El número de documento de entrada ya esta registrado',
        'error_code': 'input_document_number_registered'
    }
    default_code = 'input_document_number_registered'


# Documento de salida ya registrado

class OutputDocumentNumberRegistered(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El número de documento de salida ya esta registrado',
        'error_code': 'output_document_number_registered'
    }
    default_code = 'output_document_number_registered'


# Numero de traslado ya registrado

class TransferNumberRegistered(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El número de traslado ya esta registrado',
        'error_code': 'transfer_number_registered'
    }
    default_code = 'transfer_number_registered'


# El documento ingresado tiene que ser un numero
class InputDocumentNumberIsNotNumber(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El valor ingresado tiene que ser un numero',
        'error_code': 'input_document_number_is_not_number'
    }
    default_code = 'input_document_number_is_not_number'


# Faltan completar las cantidades de los productos en el detalle del tracker
class QuantityRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Faltan completar las cantidades de los productos en el detalle del segimiento',
        'error_code': 'quantity_required'
    }
    default_code = 'quantity_required'


# Debe existir almenos un detalle de tracker
class TrackerCompletedDetailRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Debe existir almenos un detalle de seguimiento para completar el seguimiento',
        'error_code': 'tracker_completed_detail'
    }
    default_code = 'tracker_completed_detail'

# Se requiere un numero de documento de entrada para completar el seguimiento
class InputDocumentNumberRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Se requiere un numero de documento de entrada valido para completar el seguimiento',
        'error_code': 'input_document_number_required'
    }
    default_code = 'input_document_number_required'

# Se requiere un numero de documento de salida para completar el seguimiento
class OutputDocumentNumberRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Se requiere un numero de documento valido de salida para completar el seguimiento',
        'error_code': 'output_document_number_required'
    }
    default_code = 'output_document_number_required'


# Se requiere un numero de traslado para completar el seguimiento
class TransferNumberRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Se requiere un numero de traslado valido para completar el seguimiento',
        'error_code': 'transfer_number_required'
    }
    default_code = 'transfer_number_required'

# Ingrear la informacion del operador para completar el seguimiento
class OperatorRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Ingrear la informacion del operador para completar el seguimiento',
        'error_code': 'operator_required'
    }
    default_code = 'operator_required'

# Ingresar el tipo de salida para completar el seguimiento
class OutputTypeRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Ingresar el tipo de salida para completar el seguimiento',
        'error_code': 'output_type_required'
    }
    default_code = 'output_type_required'


# Ya existe el producto de salida en el tracker
class ProductOutputRegistered(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Ya existe el producto de salida en el seguimiento',
        'error_code': 'product_output_registered'
    }
    default_code = 'product_output_registered'






