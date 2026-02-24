"""
Factories para generar datos de prueba del módulo personnel
Utiliza factory_boy para crear objetos de prueba de forma sencilla
"""
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from apps.personnel.models import PersonnelProfile

User = get_user_model()


class UserFactory:
    """Factory para crear usuarios de prueba"""

    @staticmethod
    def create(username=None, email=None, password='testpass123', **kwargs):
        if username is None:
            username = f'testuser{User.objects.count() + 1}'
        if email is None:
            email = f'{username}@example.com'
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
        return user


class AreaFactory:
    """Factory para crear áreas de prueba"""

    @staticmethod
    def create(**kwargs):
        from apps.personnel.models import Area
        defaults = {
            'code': 'OPERATIONS',
            'name': 'Operaciones',
            'description': 'Área de operaciones',
            'is_active': True
        }
        defaults.update(kwargs)
        # Use get_or_create to avoid duplicate codes
        area, created = Area.objects.get_or_create(
            code=defaults['code'],
            defaults={k: v for k, v in defaults.items() if k != 'code'}
        )
        return area


class DepartmentFactory:
    """Factory para crear departamentos de prueba"""

    @staticmethod
    def create(area=None, **kwargs):
        from apps.personnel.models import Department
        if area is None:
            area = AreaFactory.create()

        defaults = {
            'area': area,
            'name': 'Departamento de Prueba',
            'code': f'DEPT{Department.objects.count() + 1:03d}',
            'description': 'Departamento de prueba',
            'is_active': True
        }
        defaults.update(kwargs)
        return Department.objects.create(**defaults)


class DistributorCenterFactory:
    """Factory para crear centros de distribución de prueba"""

    @staticmethod
    def create(**kwargs):
        from apps.maintenance.models import DistributorCenter
        defaults = {
            'name': 'CD Prueba',
            'direction': 'Dirección de prueba',
            'country_code': 'HN'
        }
        defaults.update(kwargs)
        return DistributorCenter.objects.create(**defaults)


class PersonnelProfileFactory:
    """Factory para crear perfiles de personal"""

    @staticmethod
    def create(user=None, distributor_center=None, area=None, **kwargs):
        from apps.personnel.models import PersonnelProfile

        if distributor_center is None:
            distributor_center = DistributorCenterFactory.create()

        if area is None:
            area = AreaFactory.create()

        count = PersonnelProfile.objects.count() + 1
        defaults = {
            'user': user,  # Puede ser None
            'employee_code': f'EMP{count:04d}',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': f'juan.perez{count}@example.com',
            'distributor_center': distributor_center,
            'area': area,
            'hierarchy_level': PersonnelProfile.OPERATIVE,
            'position': 'Operador',
            'position_type': PersonnelProfile.PICKER,
            'hire_date': date.today() - timedelta(days=365),
            'contract_type': 'PERMANENT',
            'personal_id': f'0801199{count:06d}',
            'birth_date': date(1990, 1, 1),
            'gender': 'M',
            'phone': f'+504 9999-{count:04d}',
            'address': 'Dirección de prueba',
            'city': 'Tegucigalpa',
            'is_active': True
        }
        defaults.update(kwargs)
        return PersonnelProfile.objects.create(**defaults)

    @staticmethod
    def create_with_user(**kwargs):
        """Crea un perfil con usuario asociado"""
        username = kwargs.pop('username', f'user{PersonnelProfile.objects.count() + 1}')
        user = UserFactory.create(username=username)
        return PersonnelProfileFactory.create(user=user, **kwargs)

    @staticmethod
    def create_supervisor(user=None, **kwargs):
        """Crea un supervisor"""
        if user is None:
            user = UserFactory.create(username='supervisor')
        defaults = {
            'user': user,
            'hierarchy_level': PersonnelProfile.SUPERVISOR,
            'position': 'Supervisor de Turno',
            'position_type': PersonnelProfile.ADMINISTRATIVE
        }
        defaults.update(kwargs)
        return PersonnelProfileFactory.create(**defaults)

    @staticmethod
    def create_area_manager(user=None, **kwargs):
        """Crea un jefe de área"""
        if user is None:
            user = UserFactory.create(username='area_manager')
        defaults = {
            'user': user,
            'hierarchy_level': PersonnelProfile.AREA_MANAGER,
            'position': 'Jefe de Área',
            'position_type': PersonnelProfile.ADMINISTRATIVE
        }
        defaults.update(kwargs)
        return PersonnelProfileFactory.create(**defaults)

    @staticmethod
    def create_cd_manager(user=None, **kwargs):
        """Crea un gerente de CD"""
        if user is None:
            user = UserFactory.create(username='cd_manager')
        defaults = {
            'user': user,
            'hierarchy_level': PersonnelProfile.CD_MANAGER,
            'position': 'Gerente de Centro de Distribución',
            'position_type': PersonnelProfile.ADMINISTRATIVE
        }
        defaults.update(kwargs)
        return PersonnelProfileFactory.create(**defaults)


class EmergencyContactFactory:
    """Factory para crear contactos de emergencia"""

    @staticmethod
    def create(personnel=None, **kwargs):
        from apps.personnel.models import EmergencyContact

        if personnel is None:
            personnel = PersonnelProfileFactory.create()

        defaults = {
            'personnel': personnel,
            'name': 'María García',
            'relationship': 'SPOUSE',
            'phone': '+504 8888-8888',
            'is_primary': True
        }
        defaults.update(kwargs)
        return EmergencyContact.objects.create(**defaults)


class MedicalRecordFactory:
    """Factory para crear registros médicos"""

    @staticmethod
    def create(personnel=None, created_by=None, **kwargs):
        from apps.personnel.models import MedicalRecord

        if personnel is None:
            personnel = PersonnelProfileFactory.create()

        if created_by is None and not kwargs.get('created_by'):
            created_by = UserFactory.create(username='hr_user')

        defaults = {
            'personnel': personnel,
            'record_type': MedicalRecord.CHECKUP,
            'record_date': date.today(),
            'description': 'Chequeo médico de rutina',
            'created_by': created_by,
            'is_confidential': True
        }
        defaults.update(kwargs)
        return MedicalRecord.objects.create(**defaults)


class CertificationTypeFactory:
    """Factory para crear tipos de certificación"""

    @staticmethod
    def create(**kwargs):
        from apps.personnel.models import CertificationType

        defaults = {
            'name': 'Certificación de Montacargas',
            'code': f'CERT{CertificationType.objects.count() + 1:03d}',
            'description': 'Certificación para operar montacargas',
            'validity_period_days': 365,
            'requires_renewal': True,
            'is_mandatory': False,
            'is_active': True
        }
        defaults.update(kwargs)
        return CertificationType.objects.create(**defaults)


class CertificationFactory:
    """Factory para crear certificaciones"""

    @staticmethod
    def create(personnel=None, certification_type=None, created_by=None, **kwargs):
        from apps.personnel.models import Certification

        if personnel is None:
            personnel = PersonnelProfileFactory.create()

        if certification_type is None:
            certification_type = CertificationTypeFactory.create()

        if created_by is None and not kwargs.get('created_by'):
            created_by = UserFactory.create(username='hr_user')

        issue_date = kwargs.pop('issue_date', date.today() - timedelta(days=30))
        expiration_date = kwargs.pop('expiration_date', date.today() + timedelta(days=335))

        defaults = {
            'personnel': personnel,
            'certification_type': certification_type,
            'certification_number': f'CERT-{personnel.employee_code}-{certification_type.code}',
            'issuing_authority': 'Instituto de Certificación',
            'issue_date': issue_date,
            'expiration_date': expiration_date,
            'is_valid': True,
            'created_by': created_by
        }
        defaults.update(kwargs)
        return Certification.objects.create(**defaults)


class PerformanceMetricFactory:
    """Factory para crear métricas de desempeño"""

    @staticmethod
    def create(personnel=None, evaluated_by=None, **kwargs):
        from apps.personnel.models import PerformanceMetric

        if personnel is None:
            personnel = PersonnelProfileFactory.create()

        defaults = {
            'personnel': personnel,
            'metric_date': date.today(),
            'period': PerformanceMetric.DAILY,
            'pallets_moved': 100,
            'hours_worked': 8,
            'errors_count': 2,
            'accidents_count': 0,
            'supervisor_rating': 4,
            'evaluated_by': evaluated_by
        }
        defaults.update(kwargs)
        return PerformanceMetric.objects.create(**defaults)
