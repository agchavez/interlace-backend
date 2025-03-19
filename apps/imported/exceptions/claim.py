# apps/imported/exceptions/claim.py
from rest_framework.exceptions import APIException, status


class ClaimTypeInvalid(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'El tipo de reclamo es inválido',
        'error_code': 'claim_type_invalid'
    }
    default_code = 'claim_type_invalid'


class ClaimDescriptionRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'La descripción del reclamo debe tener al menos 10 caracteres',
        'error_code': 'claim_description_required'
    }
    default_code = 'claim_description_required'


class ClaimTrackerRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'El tracker asociado es obligatorio',
        'error_code': 'claim_tracker_required'
    }
    default_code = 'claim_tracker_required'


class ClaimStatusInvalid(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'El estado del reclamo es inválido',
        'error_code': 'claim_status_invalid'
    }
    default_code = 'claim_status_invalid'


class ClaimStatusTransitionInvalid(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'La transición de estado no es válida',
        'error_code': 'claim_status_transition_invalid'
    }
    default_code = 'claim_status_transition_invalid'


class FileTooLarge(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'El archivo es demasiado grande (máximo 5MB para documentos, 2MB para fotos)',
        'error_code': 'file_too_large'
    }
    default_code = 'file_too_large'


class UnsupportedFileType(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'Tipo de archivo no soportado',
        'error_code': 'file_type_unsupported'
    }
    default_code = 'file_type_unsupported'


class TooManyPhotos(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'Se ha excedido el límite de 3 fotografías por categoría',
        'error_code': 'too_many_photos'
    }
    default_code = 'too_many_photos'


class PhotoRequiredForDamage(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'message': 'Se requieren fotografías de daños cuando el tipo de reclamo es por daños',
        'error_code': 'photo_required_for_damage'
    }
    default_code = 'photo_required_for_damage'