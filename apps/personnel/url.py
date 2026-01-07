"""
URLs del módulo personnel
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.personnel_views import (
    PersonnelProfileViewSet,
    EmergencyContactViewSet,
    AreaViewSet,
)
from .views.maintenance_views import DepartmentViewSet
from .views.medical_views import MedicalRecordViewSet
from .views.certification_views import (
    CertificationViewSet,
    CertificationTypeViewSet
)
from .views.performance_views import PerformanceMetricViewSet
from .views.performance_new_views import (
    PerformanceMetricTypeViewSet,
    PerformanceEvaluationViewSet,
    EvaluationMetricValueViewSet
)

router = DefaultRouter()

# Organización
router.register(r'areas', AreaViewSet, basename='area')
router.register(r'departments', DepartmentViewSet, basename='department')

# Personal
router.register(r'profiles', PersonnelProfileViewSet, basename='personnel-profile')
router.register(
    r'emergency-contacts',
    EmergencyContactViewSet,
    basename='emergency-contact'
)

# Médico
router.register(
    r'medical-records',
    MedicalRecordViewSet,
    basename='medical-record'
)

# Certificaciones
router.register(
    r'certification-types',
    CertificationTypeViewSet,
    basename='certification-type'
)
router.register(
    r'certifications',
    CertificationViewSet,
    basename='certification'
)

# Desempeño (Sistema antiguo - mantener por compatibilidad)
router.register(
    r'performance',
    PerformanceMetricViewSet,
    basename='performance-metric'
)

# Desempeño (Sistema nuevo - Métricas escalables)
router.register(
    r'metric-types',
    PerformanceMetricTypeViewSet,
    basename='metric-type'
)
router.register(
    r'evaluations',
    PerformanceEvaluationViewSet,
    basename='evaluation'
)
router.register(
    r'evaluation-metrics',
    EvaluationMetricValueViewSet,
    basename='evaluation-metric'
)

urlpatterns = [
    path('', include(router.urls)),
]
