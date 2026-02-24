"""
Tests para los modelos del módulo personnel
"""
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.personnel.models import (
    Area, Department, PersonnelProfile, EmergencyContact,
    MedicalRecord, Certification, CertificationType, PerformanceMetric
)
from .factories import (
    AreaFactory, DepartmentFactory, PersonnelProfileFactory,
    EmergencyContactFactory, MedicalRecordFactory,
    CertificationFactory, CertificationTypeFactory,
    PerformanceMetricFactory, UserFactory, DistributorCenterFactory
)


class AreaModelTest(TestCase):
    """Tests para el modelo Area"""

    def test_create_area(self):
        """Test crear área básica"""
        area = AreaFactory.create(code='OPERATIONS', name='Operaciones')
        self.assertEqual(area.code, 'OPERATIONS')
        self.assertEqual(area.name, 'Operaciones')
        self.assertTrue(area.is_active)

    def test_area_str(self):
        """Test representación string de área"""
        area = AreaFactory.create(code='PEOPLE', name='People/RRHH')
        self.assertEqual(str(area), 'People/RRHH')

    def test_area_unique_code(self):
        """Test que el código de área sea único"""
        from django.db import IntegrityError
        from apps.personnel.models import Area
        Area.objects.create(code='UNIQUE_TEST', name='Test Area')
        with self.assertRaises(IntegrityError):
            Area.objects.create(code='UNIQUE_TEST', name='Test Area 2')


class DepartmentModelTest(TestCase):
    """Tests para el modelo Department"""

    def test_create_department(self):
        """Test crear departamento"""
        area = AreaFactory.create()
        dept = DepartmentFactory.create(
            area=area,
            name='Almacén',
            code='ALM001'
        )
        self.assertEqual(dept.area, area)
        self.assertEqual(dept.name, 'Almacén')
        self.assertTrue(dept.is_active)

    def test_department_str(self):
        """Test representación string de departamento"""
        area = AreaFactory.create(code='OPERATIONS', name='Operaciones')
        dept = DepartmentFactory.create(area=area, name='Almacén')
        self.assertIn('Operaciones', str(dept))
        self.assertIn('Almacén', str(dept))


class PersonnelProfileModelTest(TestCase):
    """Tests para el modelo PersonnelProfile"""

    def test_create_personnel_without_user(self):
        """Test crear perfil SIN usuario (operativo que no accede al sistema)"""
        personnel = PersonnelProfileFactory.create(
            user=None,
            employee_code='OPM042',
            first_name='Carlos',
            last_name='Martínez',
            hierarchy_level=PersonnelProfile.OPERATIVE
        )
        self.assertIsNone(personnel.user)
        self.assertEqual(personnel.employee_code, 'OPM042')
        self.assertEqual(personnel.full_name, 'Carlos Martínez')
        self.assertFalse(personnel.has_system_access)

    def test_create_personnel_with_user(self):
        """Test crear perfil CON usuario (supervisor con acceso)"""
        user = UserFactory.create(username='supervisor1')
        personnel = PersonnelProfileFactory.create(
            user=user,
            employee_code='SUP001',
            hierarchy_level=PersonnelProfile.SUPERVISOR
        )
        self.assertEqual(personnel.user, user)
        self.assertTrue(personnel.has_system_access)

    def test_full_name_property(self):
        """Test propiedad full_name"""
        personnel = PersonnelProfileFactory.create(
            first_name='Juan',
            last_name='Pérez'
        )
        self.assertEqual(personnel.full_name, 'Juan Pérez')

    def test_age_calculation(self):
        """Test cálculo de edad"""
        personnel = PersonnelProfileFactory.create(
            birth_date=date(1990, 1, 1)
        )
        expected_age = date.today().year - 1990
        self.assertEqual(personnel.age, expected_age)

    def test_years_of_service(self):
        """Test cálculo de años de servicio"""
        # Use replace to get exactly 3 years ago on the same date
        three_years_ago = date.today().replace(year=date.today().year - 3)
        personnel = PersonnelProfileFactory.create(
            hire_date=three_years_ago
        )
        self.assertEqual(personnel.years_of_service, 3)

    def test_hierarchy_permissions_operative(self):
        """Test permisos de aprobación para operativo"""
        personnel = PersonnelProfileFactory.create(
            hierarchy_level=PersonnelProfile.OPERATIVE
        )
        self.assertFalse(personnel.can_approve_tokens_level_1())
        self.assertFalse(personnel.can_approve_tokens_level_2())
        self.assertFalse(personnel.can_approve_tokens_level_3())

    def test_hierarchy_permissions_supervisor(self):
        """Test permisos de aprobación para supervisor"""
        personnel = PersonnelProfileFactory.create(
            hierarchy_level=PersonnelProfile.SUPERVISOR
        )
        self.assertTrue(personnel.can_approve_tokens_level_1())
        self.assertFalse(personnel.can_approve_tokens_level_2())
        self.assertFalse(personnel.can_approve_tokens_level_3())

    def test_hierarchy_permissions_area_manager(self):
        """Test permisos de aprobación para jefe de área"""
        personnel = PersonnelProfileFactory.create(
            hierarchy_level=PersonnelProfile.AREA_MANAGER
        )
        self.assertTrue(personnel.can_approve_tokens_level_1())
        self.assertTrue(personnel.can_approve_tokens_level_2())
        self.assertFalse(personnel.can_approve_tokens_level_3())

    def test_hierarchy_permissions_cd_manager(self):
        """Test permisos de aprobación para gerente CD"""
        personnel = PersonnelProfileFactory.create(
            hierarchy_level=PersonnelProfile.CD_MANAGER
        )
        self.assertTrue(personnel.can_approve_tokens_level_1())
        self.assertTrue(personnel.can_approve_tokens_level_2())
        self.assertTrue(personnel.can_approve_tokens_level_3())

    def test_supervised_personnel(self):
        """Test obtener personal supervisado directamente"""
        supervisor = PersonnelProfileFactory.create_supervisor()
        operative1 = PersonnelProfileFactory.create(immediate_supervisor=supervisor)
        operative2 = PersonnelProfileFactory.create(immediate_supervisor=supervisor)
        operative3 = PersonnelProfileFactory.create()  # Sin supervisor

        supervised = supervisor.get_supervised_personnel()
        self.assertEqual(supervised.count(), 2)
        self.assertIn(operative1, supervised)
        self.assertIn(operative2, supervised)
        self.assertNotIn(operative3, supervised)

    def test_all_subordinates_recursive(self):
        """Test obtener todos los subordinados (recursivo)"""
        # Crear jerarquía: Gerente -> Jefe Área -> Supervisor -> Operativos
        cd_manager = PersonnelProfileFactory.create_cd_manager()
        area_manager = PersonnelProfileFactory.create_area_manager(
            immediate_supervisor=cd_manager
        )
        supervisor = PersonnelProfileFactory.create_supervisor(
            immediate_supervisor=area_manager
        )
        operative1 = PersonnelProfileFactory.create(immediate_supervisor=supervisor)
        operative2 = PersonnelProfileFactory.create(immediate_supervisor=supervisor)

        # El gerente debe ver todos los subordinados
        all_subordinates = cd_manager.get_all_subordinates()
        self.assertEqual(len(all_subordinates), 4)  # Area manager, supervisor, 2 operativos


class EmergencyContactModelTest(TestCase):
    """Tests para el modelo EmergencyContact"""

    def test_create_emergency_contact(self):
        """Test crear contacto de emergencia"""
        personnel = PersonnelProfileFactory.create()
        contact = EmergencyContactFactory.create(
            personnel=personnel,
            name='María García',
            relationship='SPOUSE',
            phone='+504 9999-9999',
            is_primary=True
        )
        self.assertEqual(contact.personnel, personnel)
        self.assertEqual(contact.name, 'María García')
        self.assertTrue(contact.is_primary)


class MedicalRecordModelTest(TestCase):
    """Tests para el modelo MedicalRecord"""

    def test_create_medical_record(self):
        """Test crear registro médico"""
        personnel = PersonnelProfileFactory.create()
        user = UserFactory.create()
        record = MedicalRecordFactory.create(
            personnel=personnel,
            record_type=MedicalRecord.CHECKUP,
            created_by=user
        )
        self.assertEqual(record.personnel, personnel)
        self.assertEqual(record.record_type, MedicalRecord.CHECKUP)
        self.assertTrue(record.is_confidential)

    def test_active_incapacity(self):
        """Test verificar incapacidad activa"""
        personnel = PersonnelProfileFactory.create()
        user = UserFactory.create()

        # Incapacidad activa (no ha terminado)
        active_incapacity = MedicalRecordFactory.create(
            personnel=personnel,
            record_type=MedicalRecord.INCAPACITY,
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=3),
            created_by=user
        )
        self.assertTrue(active_incapacity.is_active_incapacity)

        # Incapacidad terminada
        past_incapacity = MedicalRecordFactory.create(
            personnel=personnel,
            record_type=MedicalRecord.INCAPACITY,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=2),
            created_by=user
        )
        self.assertFalse(past_incapacity.is_active_incapacity)


class CertificationModelTest(TestCase):
    """Tests para el modelo Certification"""

    def test_create_certification(self):
        """Test crear certificación"""
        personnel = PersonnelProfileFactory.create()
        cert_type = CertificationTypeFactory.create()
        user = UserFactory.create()

        certification = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            created_by=user
        )
        self.assertEqual(certification.personnel, personnel)
        self.assertTrue(certification.is_valid)

    def test_days_until_expiration(self):
        """Test cálculo de días hasta expiración"""
        personnel = PersonnelProfileFactory.create()
        cert_type = CertificationTypeFactory.create()
        user = UserFactory.create()

        expiration = date.today() + timedelta(days=15)
        certification = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            expiration_date=expiration,
            created_by=user
        )
        self.assertEqual(certification.days_until_expiration, 15)

    def test_is_expiring_soon(self):
        """Test verificar si expira pronto (30 días)"""
        personnel = PersonnelProfileFactory.create()
        cert_type = CertificationTypeFactory.create()
        user = UserFactory.create()

        # Expira en 20 días - es pronto
        soon = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            expiration_date=date.today() + timedelta(days=20),
            created_by=user
        )
        self.assertTrue(soon.is_expiring_soon)

        # Expira en 60 días - no es pronto
        not_soon = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            certification_number='CERT-002',
            expiration_date=date.today() + timedelta(days=60),
            created_by=user
        )
        self.assertFalse(not_soon.is_expiring_soon)

    def test_is_expired(self):
        """Test verificar si ya expiró"""
        personnel = PersonnelProfileFactory.create()
        cert_type = CertificationTypeFactory.create()
        user = UserFactory.create()

        # Ya expirada
        expired = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            expiration_date=date.today() - timedelta(days=10),
            created_by=user
        )
        self.assertTrue(expired.is_expired)

        # Aún válida
        valid = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            certification_number='CERT-003',
            expiration_date=date.today() + timedelta(days=30),
            created_by=user
        )
        self.assertFalse(valid.is_expired)


class PerformanceMetricModelTest(TestCase):
    """Tests para el modelo PerformanceMetric"""

    def test_create_performance_metric(self):
        """Test crear métrica de desempeño"""
        personnel = PersonnelProfileFactory.create()
        metric = PerformanceMetricFactory.create(
            personnel=personnel,
            pallets_moved=150,
            hours_worked=8
        )
        self.assertEqual(metric.personnel, personnel)
        self.assertEqual(metric.pallets_moved, 150)

    def test_productivity_rate_calculation(self):
        """Test cálculo automático de tasa de productividad"""
        personnel = PersonnelProfileFactory.create()
        metric = PerformanceMetricFactory.create(
            personnel=personnel,
            pallets_moved=160,
            hours_worked=8
        )
        # 160 pallets / 8 horas = 20 pallets/hora
        self.assertEqual(float(metric.productivity_rate), 20.0)

    def test_performance_score_calculation(self):
        """Test cálculo de score de desempeño"""
        personnel = PersonnelProfileFactory.create()

        # Métrica perfecta
        perfect_metric = PerformanceMetricFactory.create(
            personnel=personnel,
            pallets_moved=200,  # Alta productividad
            hours_worked=10,
            errors_count=0,     # Sin errores
            accidents_count=0,  # Sin accidentes
            supervisor_rating=5 # Máxima calificación
        )
        score = perfect_metric.performance_score
        self.assertGreater(score, 80)  # Debería ser un score alto
