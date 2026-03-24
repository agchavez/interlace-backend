"""
Excepciones personalizadas para el módulo de personal
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class PersonnelNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Personal no encontrado.'
    default_code = 'personnel_not_found'


class EmployeeCodeAlreadyExists(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El código de empleado ya existe.'
    default_code = 'employee_code_already_exists'


class UserAlreadyAssigned(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Este usuario ya tiene un perfil de personal asignado.'
    default_code = 'user_already_assigned'


class InvalidSupervisorHierarchy(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El supervisor debe tener un nivel jerárquico superior al empleado.'
    default_code = 'invalid_supervisor_hierarchy'


class DepartmentNotInArea(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El departamento no pertenece al área seleccionada.'
    default_code = 'department_not_in_area'


class MissingRequiredFields(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Faltan campos requeridos.'
    default_code = 'missing_required_fields'


class InvalidJSONData(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Los datos JSON proporcionados son inválidos.'
    default_code = 'invalid_json_data'


class ProfileCreationFailed(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error al crear el perfil de personal.'
    default_code = 'profile_creation_failed'


class AreaNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Área no encontrada.'
    default_code = 'area_not_found'


class DepartmentNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Departamento no encontrado.'
    default_code = 'department_not_found'


class EmailRequiredForUser(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El email es requerido para personal con usuario del sistema.'
    default_code = 'email_required_for_user'
