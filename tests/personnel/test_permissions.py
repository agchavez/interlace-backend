"""
Tests para los permisos personalizados del módulo personnel
"""
from django.test import TestCase, RequestFactory
from apps.personnel.permissions import (
    IsSupervisorOrAbove,
    IsAreaManagerOrAbove,
    IsCDManager,
    CanViewPersonnel,
    CanViewMedicalRecords,
    CanManagePersonnel
)
from apps.personnel.models import PersonnelProfile
from .factories import (
    PersonnelProfileFactory, UserFactory,
    MedicalRecordFactory, AreaFactory, DistributorCenterFactory
)


class IsSupervisorOrAboveTest(TestCase):
    """Tests para permiso IsSupervisorOrAbove"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsSupervisorOrAbove()

    def test_operative_no_permission(self):
        """Operativo NO tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            hierarchy_level=PersonnelProfile.OPERATIVE
        )
        request = self.factory.get('/')
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_supervisor_has_permission(self):
        """Supervisor SÍ tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_supervisor(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_area_manager_has_permission(self):
        """Jefe de área SÍ tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_area_manager(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_cd_manager_has_permission(self):
        """Gerente CD SÍ tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_cd_manager(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))


class IsAreaManagerOrAboveTest(TestCase):
    """Tests para permiso IsAreaManagerOrAbove"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAreaManagerOrAbove()

    def test_supervisor_no_permission(self):
        """Supervisor NO tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_supervisor(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_area_manager_has_permission(self):
        """Jefe de área SÍ tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_area_manager(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_cd_manager_has_permission(self):
        """Gerente CD SÍ tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_cd_manager(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))


class IsCDManagerTest(TestCase):
    """Tests para permiso IsCDManager"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsCDManager()

    def test_area_manager_no_permission(self):
        """Jefe de área NO tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_area_manager(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_cd_manager_has_permission(self):
        """Gerente CD SÍ tiene permiso"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create_cd_manager(user=user)
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))


class CanViewPersonnelTest(TestCase):
    """Tests para permiso CanViewPersonnel"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanViewPersonnel()
        self.cd = DistributorCenterFactory.create()
        self.area = AreaFactory.create()

    def test_can_view_own_profile(self):
        """Cualquiera puede ver su propio perfil"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.area
        )
        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_object_permission(request, None, personnel))

    def test_cd_manager_can_view_all_center(self):
        """Gerente CD puede ver todo su centro"""
        manager_user = UserFactory.create()
        manager = PersonnelProfileFactory.create_cd_manager(
            user=manager_user,
            distributor_center=self.cd,
            area=self.area
        )
        other_personnel = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.area
        )

        request = self.factory.get('/')
        request.user = manager_user
        self.assertTrue(self.permission.has_object_permission(request, None, other_personnel))

    def test_cd_manager_cannot_view_other_center(self):
        """Gerente CD NO puede ver personal de otro centro"""
        other_cd = DistributorCenterFactory.create(name='Otro CD')
        manager_user = UserFactory.create()
        manager = PersonnelProfileFactory.create_cd_manager(
            user=manager_user,
            distributor_center=self.cd,
            area=self.area
        )
        other_personnel = PersonnelProfileFactory.create(
            distributor_center=other_cd,
            area=self.area
        )

        request = self.factory.get('/')
        request.user = manager_user
        self.assertFalse(self.permission.has_object_permission(request, None, other_personnel))

    def test_supervisor_can_view_team(self):
        """Supervisor puede ver a su equipo"""
        supervisor_user = UserFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor(
            user=supervisor_user,
            distributor_center=self.cd,
            area=self.area
        )
        team_member = PersonnelProfileFactory.create(
            immediate_supervisor=supervisor,
            distributor_center=self.cd,
            area=self.area
        )

        request = self.factory.get('/')
        request.user = supervisor_user
        self.assertTrue(self.permission.has_object_permission(request, None, team_member))

    def test_supervisor_cannot_view_other_team(self):
        """Supervisor NO puede ver otro equipo"""
        supervisor_user = UserFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor(
            user=supervisor_user,
            distributor_center=self.cd,
            area=self.area
        )
        other_supervisor = PersonnelProfileFactory.create_supervisor(
            distributor_center=self.cd,
            area=self.area
        )
        other_team_member = PersonnelProfileFactory.create(
            immediate_supervisor=other_supervisor,
            distributor_center=self.cd,
            area=self.area
        )

        request = self.factory.get('/')
        request.user = supervisor_user
        self.assertFalse(self.permission.has_object_permission(request, None, other_team_member))


class CanViewMedicalRecordsTest(TestCase):
    """Tests para permiso CanViewMedicalRecords"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanViewMedicalRecords()
        self.cd = DistributorCenterFactory.create()
        self.people_area = AreaFactory.create(code='PEOPLE', name='People/RRHH')
        self.ops_area = AreaFactory.create(code='OPERATIONS', name='Operaciones')

    def test_can_view_own_medical_records(self):
        """Puede ver sus propios registros médicos"""
        user = UserFactory.create()
        personnel = PersonnelProfileFactory.create(
            user=user,
            distributor_center=self.cd,
            area=self.ops_area
        )
        record = MedicalRecordFactory.create(
            personnel=personnel,
            created_by=user
        )

        request = self.factory.get('/')
        request.user = user
        self.assertTrue(self.permission.has_object_permission(request, None, record))

    def test_people_area_can_view_all(self):
        """Personal de People/RRHH puede ver todos los registros"""
        hr_user = UserFactory.create()
        hr_personnel = PersonnelProfileFactory.create(
            user=hr_user,
            distributor_center=self.cd,
            area=self.people_area
        )
        other_personnel = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.ops_area
        )
        record = MedicalRecordFactory.create(
            personnel=other_personnel,
            created_by=hr_user
        )

        request = self.factory.get('/')
        request.user = hr_user
        self.assertTrue(self.permission.has_object_permission(request, None, record))

    def test_cd_manager_can_view_same_center(self):
        """Gerente CD puede ver registros de su centro"""
        manager_user = UserFactory.create()
        manager = PersonnelProfileFactory.create_cd_manager(
            user=manager_user,
            distributor_center=self.cd,
            area=self.ops_area
        )
        other_personnel = PersonnelProfileFactory.create(
            distributor_center=self.cd,
            area=self.ops_area
        )
        record = MedicalRecordFactory.create(
            personnel=other_personnel,
            created_by=manager_user
        )

        request = self.factory.get('/')
        request.user = manager_user
        self.assertTrue(self.permission.has_object_permission(request, None, record))


class CanManagePersonnelTest(TestCase):
    """Tests para permiso CanManagePersonnel"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanManagePersonnel()
        self.cd = DistributorCenterFactory.create()
        self.people_area = AreaFactory.create(code='PEOPLE', name='People/RRHH')
        self.ops_area = AreaFactory.create(code='OPERATIONS', name='Operaciones')

    def test_people_area_can_manage_all(self):
        """Personal de People/RRHH puede gestionar todo el personal"""
        hr_user = UserFactory.create()
        hr_personnel = PersonnelProfileFactory.create(
            user=hr_user,
            distributor_center=self.cd,
            area=self.people_area
        )

        request = self.factory.get('/')
        request.user = hr_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_cd_manager_can_manage(self):
        """Gerente CD puede gestionar personal"""
        manager_user = UserFactory.create()
        manager = PersonnelProfileFactory.create_cd_manager(
            user=manager_user,
            distributor_center=self.cd,
            area=self.ops_area
        )

        request = self.factory.get('/')
        request.user = manager_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_area_manager_can_manage(self):
        """Jefe de área puede gestionar personal"""
        area_manager_user = UserFactory.create()
        area_manager = PersonnelProfileFactory.create_area_manager(
            user=area_manager_user,
            distributor_center=self.cd,
            area=self.ops_area
        )

        request = self.factory.get('/')
        request.user = area_manager_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_supervisor_cannot_manage(self):
        """Supervisor NO puede gestionar personal (solo ver)"""
        supervisor_user = UserFactory.create()
        supervisor = PersonnelProfileFactory.create_supervisor(
            user=supervisor_user,
            distributor_center=self.cd,
            area=self.ops_area
        )

        request = self.factory.get('/')
        request.user = supervisor_user
        self.assertFalse(self.permission.has_permission(request, None))
