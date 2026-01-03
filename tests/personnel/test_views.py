"""
Tests para las vistas/endpoints del módulo personnel
"""
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.personnel.models import PersonnelProfile, Certification
from .factories import (
    PersonnelProfileFactory, UserFactory,
    CertificationFactory, CertificationTypeFactory,
    MedicalRecordFactory, PerformanceMetricFactory,
    EmergencyContactFactory, AreaFactory, DistributorCenterFactory
)


class PersonnelProfileViewSetTest(TestCase):
    """Tests para PersonnelProfileViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.cd = DistributorCenterFactory.create()
        self.area = AreaFactory.create()

    def test_list_personnel_unauthenticated(self):
        """Sin autenticación no se puede listar"""
        response = self.client.get('/api/profiles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_personnel_as_cd_manager(self):
        """Gerente CD puede listar todo su centro"""
        user = UserFactory.create()
        manager = PersonnelProfileFactory.create_cd_manager(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        # Crear personal del mismo centro
        personnel1 = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.area
        )
        personnel2 = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.area
        )
        # Personal de otro centro
        other_cd = DistributorCenterFactory.create(name='Otro CD')
        personnel3 = PersonnelProfileFactory.create(
            distributor_center=other_cd,
            area=self.area
        )

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/profiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debe incluir al manager y al personal del mismo centro (3 total)
        # NO debe incluir personal de otro centro
        self.assertEqual(len(response.data['results']), 3)

    def test_my_profile_endpoint(self):
        """Endpoint my_profile retorna el perfil del usuario autenticado"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            employee_code='TEST001',
            distributor_center=self.cd,
            area=self.area
        )

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/profiles/my_profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_code'], 'TEST001')

    def test_my_profile_without_personnel(self):
        """Usuario sin perfil de personal retorna 404"""
        user = UserFactory.create()

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/profiles/my_profile/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_personnel_without_user(self):
        """Crear perfil sin usuario (operativo que no accede al sistema)"""
        hr_user = UserFactory.create()
        people_area = AreaFactory.create(code='PEOPLE', name='People/RRHH')
        hr_personnel = PersonnelProfileFactory.create(
            user=hr_user,
            distributor_center=self.cd,
            area=people_area,
            hierarchy_level=PersonnelProfile.AREA_MANAGER
        )

        self.client.force_authenticate(user=hr_user)
        data = {
            'user': None,  # Sin usuario
            'employee_code': 'OPM042',
            'first_name': 'Carlos',
            'last_name': 'Martínez',
            'email': 'carlos@example.com',
            'distributor_center': self.cd.id,
            'area': self.area.id,
            'hierarchy_level': PersonnelProfile.OPERATIVE,
            'position': 'Operador de Montacargas',
            'position_type': PersonnelProfile.OPM,
            'hire_date': str(date.today()),
            'contract_type': 'PERMANENT',
            'personal_id': '0801199012345',
            'birth_date': '1990-01-01',
            'gender': 'M',
            'phone': '+504 9999-9999',
            'address': 'Dirección de prueba',
            'city': 'Tegucigalpa',
        }

        response = self.client.post('/api/profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['user'])
        self.assertEqual(response.data['employee_code'], 'OPM042')
        self.assertFalse(response.data['has_system_access'])

    def test_dashboard_endpoint(self):
        """Endpoint dashboard retorna estadísticas"""
        user = UserFactory.create()
        manager = PersonnelProfileFactory.create_cd_manager(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        # Crear personal variado
        PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.area,
            hierarchy_level=PersonnelProfile.OPERATIVE
        )
        PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.area,
            hierarchy_level=PersonnelProfile.SUPERVISOR
        )

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/profiles/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('by_hierarchy', response.data)
        self.assertIn('by_area', response.data)
        self.assertIn('certifications', response.data)

    def test_supervised_personnel_endpoint(self):
        """Endpoint supervised_personnel retorna personal supervisado"""
        user = UserFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        # Personal supervisado
        personnel1 = PersonnelProfileFactory.create(
            immediate_supervisor=supervisor,
            distributor_center=self.cd,
            area=self.area
        )
        personnel2 = PersonnelProfileFactory.create(
            immediate_supervisor=supervisor,
            distributor_center=self.cd,
            area=self.area
        )
        # Personal NO supervisado
        personnel3 = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.area
        )

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/profiles/supervised_personnel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class CertificationViewSetTest(TestCase):
    """Tests para CertificationViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.cd = DistributorCenterFactory.create()
        self.area = AreaFactory.create()

    def test_list_certifications(self):
        """Listar certificaciones"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        cert_type = CertificationTypeFactory.create()
        CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            created_by=user
        )

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/certifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_expiring_soon_endpoint(self):
        """Endpoint expiring_soon retorna certificaciones por vencer"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        cert_type = CertificationTypeFactory.create()

        # Certificación que vence en 15 días
        CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            expiration_date=date.today() + timedelta(days=15),
            created_by=user
        )
        # Certificación que vence en 60 días (no debería aparecer)
        CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            certification_number='CERT-002',
            expiration_date=date.today() + timedelta(days=60),
            created_by=user
        )

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/certifications/expiring_soon/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_revoke_certification(self):
        """Endpoint revoke revoca una certificación"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        cert_type = CertificationTypeFactory.create()
        certification = CertificationFactory.create(
            personnel=personnel,
            certification_type=cert_type,
            created_by=user
        )

        self.client.force_authenticate(user=user)
        response = self.client.post(
            f'/api/certifications/{certification.id}/revoke/',
            {'reason': 'Revocación de prueba'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        certification.refresh_from_db()
        self.assertTrue(certification.revoked)
        self.assertFalse(certification.is_valid)


class MedicalRecordViewSetTest(TestCase):
    """Tests para MedicalRecordViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.cd = DistributorCenterFactory.create()
        self.people_area = AreaFactory.create(code='PEOPLE', name='People/RRHH')

    def test_create_medical_record(self):
        """Crear registro médico"""
        hr_user = UserFactory.create()
        hr_personnel = PersonnelProfileFactory.create(
            user=hr_user,
            distributor_center=self.cd,
            area=self.people_area
        )
        patient = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.people_area
        )

        self.client.force_authenticate(user=hr_user)
        data = {
            'personnel': patient.id,
            'record_type': 'CHECKUP',
            'record_date': str(date.today()),
            'description': 'Chequeo médico de rutina',
            'is_confidential': True
        }

        response = self.client.post('/api/medical-records/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_active_incapacities_endpoint(self):
        """Endpoint active_incapacities retorna incapacidades activas"""
        hr_user = UserFactory.create()
        hr_personnel = PersonnelProfileFactory.create(
            user=hr_user,
            distributor_center=self.cd,
            area=self.people_area
        )
        patient = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.people_area
        )

        # Incapacidad activa
        MedicalRecordFactory.create(
            personnel=patient,
            record_type='INCAPACITY',
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=3),
            created_by=hr_user
        )
        # Incapacidad pasada
        MedicalRecordFactory.create(
            personnel=patient,
            record_type='INCAPACITY',
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=2),
            created_by=hr_user
        )

        self.client.force_authenticate(user=hr_user)
        response = self.client.get('/api/medical-records/active_incapacities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class PerformanceMetricViewSetTest(TestCase):
    """Tests para PerformanceMetricViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.cd = DistributorCenterFactory.create()
        self.area = AreaFactory.create()

    def test_create_performance_metric(self):
        """Supervisor puede crear métrica de desempeño"""
        supervisor_user = UserFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor(
            user=supervisor_user,
            distributor_center=self.cd,
            area=self.area
        )
        operative = PersonnelProfileFactory.create(
            immediate_supervisor=supervisor,
            distributor_center=self.cd,
            area=self.area
        )

        self.client.force_authenticate(user=supervisor_user)
        data = {
            'personnel': operative.id,
            'metric_date': str(date.today()),
            'period': 'DAILY',
            'pallets_moved': 150,
            'hours_worked': 8,
            'errors_count': 2,
            'accidents_count': 0,
            'supervisor_rating': 4,
            'evaluated_by': supervisor.id
        }

        response = self.client.post('/api/performance/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Productividad debería ser calculada automáticamente (150/8 = 18.75)
        self.assertAlmostEqual(float(response.data['productivity_rate']), 18.75)

    def test_team_performance_endpoint(self):
        """Endpoint team_performance retorna estadísticas del equipo"""
        supervisor_user = UserFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor(
            user=supervisor_user,
            distributor_center=self.cd,
            area=self.area
        )
        operative = PersonnelProfileFactory.create(
            immediate_supervisor=supervisor,
            distributor_center=self.cd,
            area=self.area
        )
        PerformanceMetricFactory.create(
            personnel=operative,
            evaluated_by=supervisor
        )

        self.client.force_authenticate(user=supervisor_user)
        response = self.client.get('/api/performance/team_performance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('team_stats', response.data)
        self.assertIn('by_person', response.data)


class ProfileCompletionViewSetTest(TestCase):
    """Tests para los endpoints de completar perfil"""

    def setUp(self):
        self.client = APIClient()
        self.cd = DistributorCenterFactory.create()
        self.area = AreaFactory.create()

    def test_my_profile_without_profile(self):
        """my_profile retorna información cuando el usuario no tiene perfil"""
        user = UserFactory.create(
            username='test_user',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/profiles/my_profile/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['has_profile'])
        self.assertEqual(response.data['message'], 'Debe completar su perfil de personal')
        self.assertEqual(response.data['user']['username'], 'test_user')
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_my_profile_with_profile(self):
        """my_profile retorna el perfil cuando el usuario tiene uno"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/profiles/my_profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], personnel.id)
        self.assertEqual(response.data['employee_code'], personnel.employee_code)

    def test_profile_completion_data(self):
        """profile_completion_data retorna todos los datos necesarios"""
        user = UserFactory.create(
            username='test_user',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/profiles/profile_completion_data/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que contenga todas las secciones
        self.assertIn('areas', response.data)
        self.assertIn('distributor_centers', response.data)
        self.assertIn('hierarchy_levels', response.data)
        self.assertIn('position_types', response.data)
        self.assertIn('contract_types', response.data)
        self.assertIn('genders', response.data)
        self.assertIn('user_info', response.data)

        # Verificar que user_info contenga los datos del usuario
        self.assertEqual(response.data['user_info']['username'], 'test_user')
        self.assertEqual(response.data['user_info']['email'], 'test@example.com')

        # Verificar que las opciones estén en el formato correcto
        self.assertGreater(len(response.data['hierarchy_levels']), 0)
        self.assertIn('value', response.data['hierarchy_levels'][0])
        self.assertIn('label', response.data['hierarchy_levels'][0])

    def test_complete_my_profile_success(self):
        """complete_my_profile crea perfil exitosamente"""
        user = UserFactory.create(
            username='new_user',
            email='new@example.com'
        )
        self.client.force_authenticate(user=user)

        data = {
            'employee_code': 'EMP999',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'email': 'nuevo@example.com',
            'distributor_center': self.cd.id,
            'area': self.area.id,
            'hierarchy_level': 'SUPERVISOR',
            'position': 'Supervisor de Turno',
            'position_type': 'ADMINISTRATIVE',
            'hire_date': str(date.today()),
            'contract_type': 'PERMANENT',
            'personal_id': '0801-1990-99999',
            'birth_date': '1990-05-20',
            'gender': 'M',
            'phone': '+504 9999-9999',
            'address': 'Col. Kennedy, Tegucigalpa',
            'city': 'Tegucigalpa'
        }

        response = self.client.post(
            '/api/profiles/complete_my_profile/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('profile', response.data)
        self.assertEqual(response.data['profile']['employee_code'], 'EMP999')

        # Verificar que el perfil fue creado y vinculado al usuario
        user.refresh_from_db()
        self.assertTrue(hasattr(user, 'personnel_profile'))
        self.assertEqual(user.personnel_profile.employee_code, 'EMP999')

    def test_complete_my_profile_already_has_profile(self):
        """complete_my_profile falla si el usuario ya tiene perfil"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        self.client.force_authenticate(user=user)

        data = {
            'employee_code': 'EMP888',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'distributor_center': self.cd.id,
            'area': self.area.id,
            'hierarchy_level': 'SUPERVISOR',
            'position': 'Supervisor',
            'position_type': 'ADMINISTRATIVE',
            'hire_date': str(date.today()),
            'contract_type': 'PERMANENT',
            'personal_id': '0801-1990-88888',
            'birth_date': '1990-01-01',
            'gender': 'M',
            'phone': '+504 8888-8888',
            'address': 'Test',
            'city': 'Test'
        }

        response = self.client.post(
            '/api/profiles/complete_my_profile/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Ya tiene un perfil creado')

    def test_complete_my_profile_validation_errors(self):
        """complete_my_profile valida los datos correctamente"""
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        # Datos incompletos
        data = {
            'employee_code': 'EMP777',
            'first_name': 'Test'
            # Faltan campos requeridos
        }

        response = self.client.post(
            '/api/profiles/complete_my_profile/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Debe retornar errores de validación
        self.assertIn('last_name', response.data)

    def test_complete_my_profile_unauthenticated(self):
        """complete_my_profile requiere autenticación"""
        data = {
            'employee_code': 'EMP666',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            '/api/profiles/complete_my_profile/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
