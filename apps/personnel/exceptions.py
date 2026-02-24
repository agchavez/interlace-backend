"""
Excepciones personalizadas para el módulo de personal
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class PersonnelNotFound(APIException):
    """Excepción cuando no se encuentra el personal"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {
        'mensage': 'Personal no encontrado.',
        'error_code': 'personnel_not_found'
    }
    default_code = 'personnel_not_found'


class EmployeeCodeAlreadyExists(APIException):
    """Excepción cuando el código de empleado ya existe"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El código de empleado ya existe.',
        'error_code': 'employee_code_already_exists'
    }
    default_code = 'employee_code_already_exists'


class UserAlreadyAssigned(APIException):
    """Excepción cuando el usuario ya tiene un perfil asignado"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Este usuario ya tiene un perfil de personal asignado.',
        'error_code': 'user_already_assigned'
    }
    default_code = 'user_already_assigned'


class InvalidSupervisorHierarchy(APIException):
    """Excepción cuando el supervisor no tiene nivel jerárquico superior"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El supervisor debe tener un nivel jerárquico superior al empleado.',
        'error_code': 'invalid_supervisor_hierarchy'
    }
    default_code = 'invalid_supervisor_hierarchy'


class DepartmentNotInArea(APIException):
    """Excepción cuando el departamento no pertenece al área"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El departamento no pertenece al área seleccionada.',
        'error_code': 'department_not_in_area'
    }
    default_code = 'department_not_in_area'


class MissingRequiredFields(APIException):
    """Excepción cuando faltan campos requeridos"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Faltan campos requeridos.',
        'error_code': 'missing_required_fields'
    }
    default_code = 'missing_required_fields'


class InvalidJSONData(APIException):
    """Excepción cuando los datos JSON son inválidos"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Los datos JSON proporcionados son inválidos.',
        'error_code': 'invalid_json_data'
    }
    default_code = 'invalid_json_data'


class ProfileCreationFailed(APIException):
    """Excepción cuando falla la creación del perfil"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'Error al crear el perfil de personal.',
        'error_code': 'profile_creation_failed'
    }
    default_code = 'profile_creation_failed'


class AreaNotFound(APIException):
    """Excepción cuando no se encuentra el área"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {
        'mensage': 'Área no encontrada.',
        'error_code': 'area_not_found'
    }
    default_code = 'area_not_found'


class DepartmentNotFound(APIException):
    """Excepción cuando no se encuentra el departamento"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {
        'mensage': 'Departamento no encontrado.',
        'error_code': 'department_not_found'
    }
    default_code = 'department_not_found'


class EmailRequiredForUser(APIException):
    """Excepción cuando falta email para personal con usuario"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'mensage': 'El email es requerido para personal con usuario del sistema.',
        'error_code': 'email_required_for_user'
    }
    default_code = 'email_required_for_user'
