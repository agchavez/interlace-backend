# Carga Masiva de Personal desde Excel (Campos Obligatorios)

Este documento detalla únicamente los **campos obligatorios** para la carga masiva de personal y registros médicos, según los modelos actuales del sistema.

## 1. Personal (PersonnelProfile)

### Campos obligatorios
- **employee_code**: Código único del empleado (ej: 22144, SUP001, OPM042)
- **first_name**: Nombres
- **last_name**: Apellidos
- **primary_distributor_center**: Centro de distribución principal (ID o nombre exacto)
- **area**: Área de negocio (ID o nombre exacto)
- **hierarchy_level**: Nivel jerárquico (OPERATIVE, SUPERVISOR, AREA_MANAGER, CD_MANAGER)
- **position**: Puesto actual
- **position_type**: Tipo de posición (PICKER, COUNTER, OPM, YARD_DRIVER, LOADER, WAREHOUSE_ASSISTANT, SECURITY_GUARD, DELIVERY_DRIVER, ADMINISTRATIVE, OTHER)
- **hire_date**: Fecha de ingreso (YYYY-MM-DD)
- **personal_id**: Número de identidad (13 dígitos)
- **birth_date**: Fecha de nacimiento (YYYY-MM-DD)
- **gender**: Género (M, F, OTHER)
- **phone**: Teléfono
- **address**: Dirección residencial
- **city**: Ciudad

## 2. Historial Médico (MedicalRecord)

### Campos obligatorios
- **personnel**: Código de empleado (debe existir en la carga de personal)
- **record_type**: Tipo de registro (CONDITION, CLINIC_PASS, INCAPACITY, CHECKUP)
- **record_date**: Fecha del registro (YYYY-MM-DD)
- **description**: Descripción general del evento médico

---

**Notas:**
- Los valores de campos tipo elección (choices) deben coincidir exactamente con los valores indicados en mayúsculas.
- Para relaciones (FK), se recomienda usar el código o nombre exacto del registro relacionado.
- Las fechas deben estar en formato `YYYY-MM-DD`.

Si tienes dudas sobre algún campo, consulta con el equipo de desarrollo o revisa los modelos en el sistema.
