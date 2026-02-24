# Tests del Módulo Personnel

Suite completa de tests para el módulo de gestión de personal (People Scorecard).

## 📁 Estructura de Tests

```
apps/personnel/tests/
├── __init__.py
├── README.md                    # Este archivo
├── factories.py                 # Factories para generar datos de prueba
├── test_models.py               # Tests de modelos
├── test_serializers.py          # Tests de serializers
├── test_permissions.py          # Tests de permisos
└── test_views.py                # Tests de vistas/endpoints
```

## 🚀 Ejecutar Tests

### Ejecutar todos los tests del módulo personnel

```bash
python manage.py test apps.personnel
```

### Ejecutar un archivo específico de tests

```bash
# Tests de modelos
python manage.py test apps.personnel.tests.test_models

# Tests de serializers
python manage.py test apps.personnel.tests.test_serializers

# Tests de permisos
python manage.py test apps.personnel.tests.test_permissions

# Tests de vistas/endpoints
python manage.py test apps.personnel.tests.test_views
```

### Ejecutar una clase específica de tests

```bash
python manage.py test apps.personnel.tests.test_models.PersonnelProfileModelTest
```

### Ejecutar un test específico

```bash
python manage.py test apps.personnel.tests.test_models.PersonnelProfileModelTest.test_create_personnel_without_user
```

### Ver cobertura de tests

```bash
# Instalar coverage
pip install coverage

# Ejecutar tests con coverage
coverage run --source='apps.personnel' manage.py test apps.personnel
coverage report
coverage html  # Genera reporte HTML en htmlcov/
```

## 📋 Cobertura de Tests

### 1. **test_models.py** - Tests de Modelos

#### AreaModelTest
- ✅ Crear área básica
- ✅ Representación string
- ✅ Validación de código único

#### DepartmentModelTest
- ✅ Crear departamento
- ✅ Representación string

#### PersonnelProfileModelTest ⭐ **Crítico**
- ✅ Crear perfil SIN usuario (operativo sin acceso al sistema)
- ✅ Crear perfil CON usuario (supervisor con acceso)
- ✅ Propiedad `full_name`
- ✅ Propiedad `has_system_access`
- ✅ Cálculo de edad
- ✅ Cálculo de años de servicio
- ✅ Permisos de aprobación por nivel jerárquico:
  - Operativo (no puede aprobar)
  - Supervisor (nivel 1)
  - Jefe de Área (niveles 1-2)
  - Gerente CD (niveles 1-3)
- ✅ Obtener personal supervisado directamente
- ✅ Obtener todos los subordinados (recursivo)

#### EmergencyContactModelTest
- ✅ Crear contacto de emergencia

#### MedicalRecordModelTest
- ✅ Crear registro médico
- ✅ Verificar incapacidad activa
- ✅ Verificar incapacidad pasada

#### CertificationModelTest
- ✅ Crear certificación
- ✅ Calcular días hasta expiración
- ✅ Verificar si expira pronto (30 días)
- ✅ Verificar si ya expiró

#### PerformanceMetricModelTest
- ✅ Crear métrica de desempeño
- ✅ Cálculo automático de tasa de productividad
- ✅ Cálculo de score de desempeño

---

### 2. **test_serializers.py** - Tests de Serializers

#### PersonnelProfileSerializerTest
- ✅ Serializar perfil sin usuario
- ✅ Serializar perfil con usuario
- ✅ Serializer de detalle (con datos anidados)
- ✅ Validación: supervisor debe tener nivel superior

#### EmergencyContactSerializerTest
- ✅ Serializar contacto de emergencia

#### MedicalRecordSerializerTest
- ✅ Serializar registro médico
- ✅ Validación: incapacidades requieren fechas de inicio y fin

#### CertificationSerializerTest
- ✅ Serializar certificación
- ✅ Validación: fecha de expiración debe ser posterior a emisión

#### PerformanceMetricSerializerTest
- ✅ Serializar métrica de desempeño
- ✅ Validación: rating debe estar entre 1 y 5

---

### 3. **test_permissions.py** - Tests de Permisos

#### IsSupervisorOrAboveTest
- ✅ Operativo NO tiene permiso
- ✅ Supervisor SÍ tiene permiso
- ✅ Jefe de área SÍ tiene permiso
- ✅ Gerente CD SÍ tiene permiso

#### IsAreaManagerOrAboveTest
- ✅ Supervisor NO tiene permiso
- ✅ Jefe de área SÍ tiene permiso
- ✅ Gerente CD SÍ tiene permiso

#### IsCDManagerTest
- ✅ Jefe de área NO tiene permiso
- ✅ Gerente CD SÍ tiene permiso

#### CanViewPersonnelTest ⭐ **Crítico**
- ✅ Cualquiera puede ver su propio perfil
- ✅ Gerente CD puede ver todo su centro
- ✅ Gerente CD NO puede ver otro centro
- ✅ Supervisor puede ver a su equipo
- ✅ Supervisor NO puede ver otro equipo

#### CanViewMedicalRecordsTest
- ✅ Puede ver sus propios registros médicos
- ✅ Personal de People/RRHH puede ver todos los registros
- ✅ Gerente CD puede ver registros de su centro

#### CanManagePersonnelTest
- ✅ Personal de People/RRHH puede gestionar todo
- ✅ Gerente CD puede gestionar
- ✅ Jefe de área puede gestionar
- ✅ Supervisor NO puede gestionar (solo ver)

---

### 4. **test_views.py** - Tests de Vistas/Endpoints API

#### PersonnelProfileViewSetTest
- ✅ Sin autenticación no se puede listar
- ✅ Gerente CD puede listar todo su centro
- ✅ Endpoint `/my_profile/` retorna perfil del usuario
- ✅ Usuario sin perfil retorna 404
- ✅ Crear perfil sin usuario (operativo) ⭐
- ✅ Endpoint `/dashboard/` retorna estadísticas
- ✅ Endpoint `/supervised_personnel/` retorna equipo supervisado

#### CertificationViewSetTest
- ✅ Listar certificaciones
- ✅ Endpoint `/expiring_soon/` retorna certificaciones por vencer
- ✅ Endpoint `/revoke/` revoca una certificación

#### MedicalRecordViewSetTest
- ✅ Crear registro médico
- ✅ Endpoint `/active_incapacities/` retorna incapacidades activas

#### PerformanceMetricViewSetTest
- ✅ Supervisor puede crear métrica de desempeño
- ✅ Cálculo automático de productividad
- ✅ Endpoint `/team_performance/` retorna estadísticas del equipo

---

## 🏭 Uso de Factories

Los factories facilitan la creación de datos de prueba. Ejemplos:

```python
from apps.personnel.tests.factories import (
    PersonnelProfileFactory, UserFactory, CertificationFactory
)

# Crear operativo SIN usuario (no accede al sistema)
operative = PersonnelProfileFactory.create(
    user=None,
    employee_code='OPM042',
    hierarchy_level=PersonnelProfile.OPERATIVE
)

# Crear supervisor CON usuario
supervisor_user = UserFactory.create(username='supervisor1')
supervisor = PersonnelProfileFactory.create_supervisor(user=supervisor_user)

# Crear jerarquía completa
cd_manager = PersonnelProfileFactory.create_cd_manager()
area_manager = PersonnelProfileFactory.create_area_manager(
    immediate_supervisor=cd_manager
)
supervisor = PersonnelProfileFactory.create_supervisor(
    immediate_supervisor=area_manager
)
operative1 = PersonnelProfileFactory.create(immediate_supervisor=supervisor)
operative2 = PersonnelProfileFactory.create(immediate_supervisor=supervisor)

# Crear certificación
certification = CertificationFactory.create(
    personnel=operative1,
    expiration_date=date.today() + timedelta(days=15)
)
```

## ✅ Test Coverage Goals

| Componente | Coverage Goal |
|------------|---------------|
| Modelos | 95%+ |
| Serializers | 90%+ |
| Permisos | 100% |
| Vistas | 85%+ |
| **Total** | **90%+** |

## 🔍 Casos de Uso Críticos Testeados

### ✅ Caso 1: Personal sin Usuario
**Escenario**: Operativo que NO tiene acceso al sistema. El supervisor solicita tokens por él.

```python
def test_create_personnel_without_user(self):
    """Operativo sin usuario del sistema"""
    personnel = PersonnelProfileFactory.create(
        user=None,  # ⭐ Sin usuario
        employee_code='OPM042',
        hierarchy_level=PersonnelProfile.OPERATIVE
    )
    self.assertFalse(personnel.has_system_access)
```

### ✅ Caso 2: Jerarquía de Aprobaciones
**Escenario**: Verificar niveles de aprobación según jerarquía.

```python
def test_hierarchy_permissions(self):
    supervisor = PersonnelProfileFactory.create_supervisor()
    self.assertTrue(supervisor.can_approve_tokens_level_1())  # ✅
    self.assertFalse(supervisor.can_approve_tokens_level_2()) # ❌
```

### ✅ Caso 3: Permisos por Centro
**Escenario**: Gerente solo ve su centro.

```python
def test_cd_manager_cannot_view_other_center(self):
    manager = PersonnelProfileFactory.create_cd_manager(distributor_center=cd1)
    other_personnel = PersonnelProfileFactory.create(distributor_center=cd2)
    # Manager NO puede ver personal de otro centro
    self.assertFalse(permission.has_object_permission(request, None, other_personnel))
```

## 🐛 Ejecutar Tests en Debug Mode

```bash
# Con breakpoint en pdb
python -m pdb manage.py test apps.personnel.tests.test_models

# Con verbose output
python manage.py test apps.personnel --verbosity=2
```

## 📊 Generar Reporte de Cobertura

```bash
coverage run --source='apps.personnel' manage.py test apps.personnel
coverage html
# Abrir htmlcov/index.html en el navegador
```

## ⚠️ Notas Importantes

1. **Base de Datos de Test**: Django crea una base de datos temporal para tests. NO afecta la base de datos de desarrollo.

2. **Datos de Prueba**: Todos los datos se crean con factories y se limpian automáticamente después de cada test.

3. **Independencia**: Cada test es independiente y puede ejecutarse solo.

4. **Performance**: Los tests están optimizados con `select_related` y `prefetch_related` donde es necesario.

## 🔗 Integración Continua

Para CI/CD, agregar al pipeline:

```yaml
# .github/workflows/tests.yml
- name: Run Personnel Tests
  run: |
    python manage.py test apps.personnel --verbosity=2
    coverage run --source='apps.personnel' manage.py test apps.personnel
    coverage report --fail-under=90
```

---

## 📚 Referencias

- [Django Testing Documentation](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
