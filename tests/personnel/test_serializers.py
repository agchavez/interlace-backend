"""
Tests para los serializers del módulo personnel
"""
from datetime import date, timedelta
from django.test import TestCase
from apps.personnel.serializers import (
    PersonnelProfileListSerializer,
    PersonnelProfileDetailSerializer,
    PersonnelProfileCreateUpdateSerializer,
    EmergencyContactSerializer,
    MedicalRecordSerializer,
    CertificationSerializer,
    PerformanceMetricSerializer
)
from .factories import (
    PersonnelProfileFactory, EmergencyContactFactory,
    MedicalRecordFactory, CertificationFactory,
    PerformanceMetricFactory, UserFactory,
    CertificationTypeFactory, AreaFactory, DepartmentFactory
)


class PersonnelProfileSerializerTest(TestCase):
    """Tests para serializers de PersonnelProfile"""

    def test_list_serializer_without_user(self):
        """Test serializar perfil sin usuario"""
        personnel = PersonnelProfileFactory.create(
            user=None,
            employee_code='OPM042',
            first_name='Carlos',
            last_name='Martínez'
        )
        serializer = PersonnelProfileListSerializer(personnel)
        data = serializer.data

        self.assertEqual(data['employee_code'], 'OPM042')
        self.assertEqual(data['full_name'], 'Carlos Martínez')
        self.assertFalse(data['has_system_access'])
        self.assertIsNone(data['username'])

    def test_list_serializer_with_user(self):
        """Test serializar perfil con usuario"""
        user = UserFactory.create(username='testuser')
        personnel = PersonnelProfileFactory.create(user=user)
        serializer = PersonnelProfileListSerializer(personnel)
        data = serializer.data

        self.assertTrue(data['has_system_access'])
        self.assertEqual(data['username'], 'testuser')

    def test_detail_serializer(self):
        """Test serializer de detalle"""
        supervisor = PersonnelProfileFactory.create_supervisor()
        personnel = PersonnelProfileFactory.create(
            immediate_supervisor=supervisor
        )
        EmergencyContactFactory.create(personnel=personnel)

        serializer = PersonnelProfileDetailSerializer(personnel)
        data = serializer.data

        self.assertIn('user_data', data)
        self.assertIn('area_data', data)
        self.assertIn('supervisor_data', data)
        self.assertIn('emergency_contacts', data)
        self.assertIn('can_approve_level_1', data)
        self.assertEqual(len(data['emergency_contacts']), 1)

    def test_create_serializer_validation_supervisor_hierarchy(self):
        """Test validación: supervisor debe tener nivel superior"""
        from apps.personnel.models import PersonnelProfile
        operative = PersonnelProfileFactory.create(
            hierarchy_level=PersonnelProfile.OPERATIVE
        )
        area = AreaFactory.create()

        # Intentar asignar un operativo como supervisor de otro
        data = {
            'employee_code': 'EMP999',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'hierarchy_level': PersonnelProfile.OPERATIVE,
            'immediate_supervisor': operative.id,
            'area': area.id,
            # ... otros campos requeridos
        }

        serializer = PersonnelProfileDetailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('immediate_supervisor', serializer.errors)


class EmergencyContactSerializerTest(TestCase):
    """Tests para EmergencyContactSerializer"""

    def test_serialize_emergency_contact(self):
        """Test serializar contacto de emergencia"""
        contact = EmergencyContactFactory.create(
            name='María García',
            relationship='SPOUSE',
            phone='+504 9999-9999'
        )
        serializer = EmergencyContactSerializer(contact)
        data = serializer.data

        self.assertEqual(data['name'], 'María García')
        self.assertEqual(data['relationship'], 'SPOUSE')
        self.assertIn('relationship_display', data)


class MedicalRecordSerializerTest(TestCase):
    """Tests para MedicalRecordSerializer"""

    def test_serialize_medical_record(self):
        """Test serializar registro médico"""
        personnel = PersonnelProfileFactory.create()
        user = UserFactory.create()
        record = MedicalRecordFactory.create(
            personnel=personnel,
            record_type='CHECKUP',
            created_by=user
        )
        serializer = MedicalRecordSerializer(record)
        data = serializer.data

        self.assertEqual(data['record_type'], 'CHECKUP')
        self.assertIn('record_type_display', data)
        self.assertIn('personnel_name', data)
        self.assertTrue(data['is_confidential'])

    def test_validation_incapacity_dates(self):
        """Test validación: incapacidades requieren fechas"""
        personnel = PersonnelProfileFactory.create()
        user = UserFactory.create()

        data = {
            'personnel': personnel.id,
            'record_type': 'INCAPACITY',
            'record_date': date.today(),
            'description': 'Incapacidad',
            'created_by': user.id
            # Falta start_date y end_date
        }

        serializer = MedicalRecordSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class CertificationSerializerTest(TestCase):
    """Tests para CertificationSerializer"""

    def test_serialize_certification(self):
        """Test serializar certificación"""
        personnel = PersonnelProfileFactory.create()
        cert_type = CertificationTypeFactory.create()
        user = UserFactory.create()

        certification = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            expiration_date=date.today() + timedelta(days=15),
            created_by=user
        )
        serializer = CertificationSerializer(certification)
        data = serializer.data

        self.assertIn('certification_type_name', data)
        self.assertIn('days_until_expiration', data)
        self.assertIn('status_display', data)
        self.assertTrue(data['is_expiring_soon'])

    def test_validation_expiration_after_issue(self):
        """Test validación: expiración debe ser después de emisión"""
        personnel = PersonnelProfileFactory.create()
        cert_type = CertificationTypeFactory.create()
        user = UserFactory.create()

        data = {
            'personnel': personnel.id,
            'certification_type': cert_type.id,
            'certification_number': 'CERT001',
            'issuing_authority': 'Autoridad Test',
            'issue_date': date.today(),
            'expiration_date': date.today() - timedelta(days=1),  # Antes de emisión!
            'created_by': user.id
        }

        serializer = CertificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('expiration_date', serializer.errors)


class PerformanceMetricSerializerTest(TestCase):
    """Tests para PerformanceMetricSerializer"""

    def test_serialize_performance_metric(self):
        """Test serializar métrica de desempeño"""
        personnel = PersonnelProfileFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor()

        metric = PerformanceMetricFactory.create(
            personnel=personnel,
            pallets_moved=160,
            hours_worked=8,
            supervisor_rating=4,
            evaluated_by=supervisor
        )
        serializer = PerformanceMetricSerializer(metric)
        data = serializer.data

        self.assertEqual(data['pallets_moved'], 160)
        self.assertIn('productivity_rate', data)
        self.assertIn('performance_score', data)
        self.assertIn('period_display', data)

    def test_validation_rating_range(self):
        """Test validación: rating debe estar entre 1 y 5"""
        personnel = PersonnelProfileFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor()

        data = {
            'personnel': personnel.id,
            'metric_date': date.today(),
            'period': 'DAILY',
            'pallets_moved': 100,
            'hours_worked': 8,
            'supervisor_rating': 6,  # Fuera de rango!
            'evaluated_by': supervisor.id
        }

        serializer = PerformanceMetricSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('supervisor_rating', serializer.errors)
