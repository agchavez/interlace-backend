"""
Serializers para modelos de personal
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models.personnel import PersonnelProfile, EmergencyContact
from ..models.organization import Area, Department
from apps.core.azure_utils import get_photo_url_with_sas
from ..exceptions import (
    InvalidSupervisorHierarchy,
    DepartmentNotInArea,
    UserAlreadyAssigned,
    EmailRequiredForUser
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico de usuario"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = fields


class AreaSerializer(serializers.ModelSerializer):
    """Serializer de Áreas"""
    display_name = serializers.CharField(source='get_code_display', read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'code', 'name', 'display_name', 'description', 'is_active']
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer de Departamentos"""
    area_name = serializers.CharField(source='area.get_code_display', read_only=True)
    code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=50,
        help_text='Se genera automáticamente si no se proporciona'
    )

    class Meta:
        model = Department
        fields = ['id', 'area', 'area_name', 'name', 'code', 'description', 'is_active']
        read_only_fields = ['id']

    def _generate_department_code(self, area, name):
        """
        Genera un código único para el departamento basado en el área y nombre
        Formato: DEPT-{AREA_PREFIX}-{SEQUENTIAL}
        Ejemplo: DEPT-OPE-001, DEPT-ADM-002
        """
        # Obtener prefijo del área (primeras 3 letras)
        area_prefix = area.code[:3].upper()

        # Obtener el número secuencial más alto para este área
        existing_depts = Department.objects.filter(
            code__startswith=f'DEPT-{area_prefix}-'
        ).order_by('-code')

        if existing_depts.exists():
            # Extraer el número del último código
            last_code = existing_depts.first().code
            try:
                last_number = int(last_code.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Generar el código
        code = f'DEPT-{area_prefix}-{next_number:03d}'

        # Verificar que sea único (por si acaso)
        while Department.objects.filter(code=code).exists():
            next_number += 1
            code = f'DEPT-{area_prefix}-{next_number:03d}'

        return code

    def create(self, validated_data):
        """Sobrescribe create para auto-generar el código si no se proporciona"""
        # Si code no está presente, es None, o es cadena vacía, generarlo
        code = validated_data.get('code')
        if not code:
            from apps.personnel.models import Area

            area = validated_data.get('area')
            # Si area es un ID, obtener la instancia
            if isinstance(area, int):
                area = Area.objects.get(id=area)

            name = validated_data.get('name')
            validated_data['code'] = self._generate_department_code(area, name)

        return super().create(validated_data)


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer de contactos de emergencia"""
    relationship_display = serializers.CharField(
        source='get_relationship_display',
        read_only=True
    )

    class Meta:
        model = EmergencyContact
        fields = [
            'id', 'personnel', 'name', 'relationship', 'relationship_display',
            'phone', 'alternate_phone', 'address', 'is_primary', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'personnel': {'write_only': True}
        }


class PersonnelProfileAutocompleteSerializer(serializers.ModelSerializer):
    """
    Serializer mínimo para autocompletes / dropdowns.
    Solo incluye los campos necesarios para mostrar el item en una lista.
    No hace queries adicionales ni accede a relaciones pesadas.
    """
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = PersonnelProfile
        fields = [
            'id',
            'employee_code',
            'full_name',
            'first_name',
            'last_name',
            'position',
            'position_type',
        ]
        read_only_fields = fields


class PersonnelProfileListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    full_name = serializers.CharField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    has_system_access = serializers.BooleanField(read_only=True)
    hierarchy_level_display = serializers.CharField(
        source='get_hierarchy_level_display',
        read_only=True
    )
    position_type_display = serializers.CharField(
        source='get_position_type_display',
        read_only=True
    )
    center_name = serializers.CharField(
        source='primary_distributor_center.name',
        read_only=True
    )
    distributor_centers_names = serializers.SerializerMethodField()
    area_name = serializers.CharField(
        source='area.get_code_display',
        read_only=True
    )
    department_name = serializers.CharField(
        source='department.name',
        read_only=True,
        allow_null=True
    )
    supervisor_name = serializers.CharField(
        source='immediate_supervisor.full_name',
        read_only=True,
        allow_null=True
    )

    # Indicadores
    years_of_service = serializers.SerializerMethodField()
    has_valid_certifications = serializers.BooleanField(read_only=True)
    certifications_count = serializers.SerializerMethodField()
    certifications_expiring_count = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    authentication_methods = serializers.SerializerMethodField()
    is_profile_complete = serializers.SerializerMethodField()

    class Meta:
        model = PersonnelProfile
        fields = [
            'id', 'employee_code', 'user', 'username', 'user_email', 'email',
            'full_name', 'first_name', 'last_name', 'has_system_access',
            'hierarchy_level', 'hierarchy_level_display',
            'position', 'position_type', 'position_type_display',
            'center_name', 'distributor_centers_names', 'area_name', 'department_name',
            'supervisor_name', 'hire_date', 'is_active',
            'years_of_service', 'has_valid_certifications', 'certifications_count',
            'certifications_expiring_count', 'phone', 'photo_url', 'authentication_methods',
            'is_profile_complete'
        ]
        read_only_fields = fields

    def get_years_of_service(self, obj):
        if not obj.hire_date:
            return 0
        from datetime import date
        today = date.today()
        return today.year - obj.hire_date.year - (
            (today.month, today.day) < (obj.hire_date.month, obj.hire_date.day)
        )

    def get_certifications_count(self, obj):
        return obj.certifications.filter(is_valid=True).count()

    def get_certifications_expiring_count(self, obj):
        return obj.certifications_expiring_soon.count()

    def get_distributor_centers_names(self, obj):
        return [center.name for center in obj.distributor_centers.all()]

    def get_photo_url(self, obj):
        """Devuelve la URL completa de la foto con SAS token"""
        if obj.photo:
            # Generar URL con SAS token para acceso seguro
            return get_photo_url_with_sas(obj.photo)
        return None

    def get_authentication_methods(self, obj):
        """Devuelve los métodos de autenticación disponibles para este usuario"""
        methods = []

        if obj.user:
            # Si tiene usuario, puede autenticarse
            if obj.user.email:
                methods.append({
                    'type': 'email',
                    'value': obj.user.email,
                    'label': 'Correo electrónico',
                    'enabled': True
                })

            if obj.user.username:
                methods.append({
                    'type': 'username',
                    'value': obj.user.username,
                    'label': 'Nombre de usuario',
                    'enabled': True
                })

        return methods

    def get_is_profile_complete(self, obj):
        """Verifica si el perfil tiene la información clave completa."""
        return bool(
            obj.first_name
            and obj.last_name
            and obj.employee_code
            and obj.birth_date
            and obj.gender
            and obj.phone
            and obj.personal_id
            and obj.hire_date
            and obj.position
            and obj.area_id
        )


class PersonnelProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle"""
    user_data = UserBasicSerializer(source='user', read_only=True)
    area_data = AreaSerializer(source='area', read_only=True)
    department_data = DepartmentSerializer(source='department', read_only=True)
    primary_distributor_center_data = serializers.SerializerMethodField()
    distributor_centers_data = serializers.SerializerMethodField()
    supervisor_data = serializers.SerializerMethodField()
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)

    # Displays
    hierarchy_level_display = serializers.CharField(
        source='get_hierarchy_level_display',
        read_only=True
    )
    position_type_display = serializers.CharField(
        source='get_position_type_display',
        read_only=True
    )
    gender_display = serializers.CharField(
        source='get_gender_display',
        read_only=True
    )
    marital_status_display = serializers.CharField(
        source='get_marital_status_display',
        read_only=True
    )
    contract_type_display = serializers.CharField(
        source='get_contract_type_display',
        read_only=True
    )

    # Propiedades calculadas
    full_name = serializers.CharField(read_only=True)
    has_system_access = serializers.BooleanField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    years_of_service = serializers.IntegerField(read_only=True)
    has_valid_certifications = serializers.BooleanField(read_only=True)
    photo_url = serializers.SerializerMethodField()

    # Estadísticas
    certifications_count = serializers.SerializerMethodField()
    certifications_expiring_count = serializers.SerializerMethodField()
    medical_records_count = serializers.SerializerMethodField()
    supervised_count = serializers.SerializerMethodField()

    # Permisos
    can_approve_level_1 = serializers.SerializerMethodField()
    can_approve_level_2 = serializers.SerializerMethodField()
    can_approve_level_3 = serializers.SerializerMethodField()

    # Métodos de autenticación disponibles
    authentication_methods = serializers.SerializerMethodField()

    class Meta:
        model = PersonnelProfile
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'age', 'years_of_service', 'has_valid_certifications'
        ]

    def get_primary_distributor_center_data(self, obj):
        if obj.primary_distributor_center:
            return {
                'id': obj.primary_distributor_center.id,
                'name': obj.primary_distributor_center.name,
                'code': getattr(obj.primary_distributor_center, 'code', None)
            }
        return None

    def get_distributor_centers_data(self, obj):
        return [
            {
                'id': center.id,
                'name': center.name,
                'code': getattr(center, 'code', None)
            }
            for center in obj.distributor_centers.all()
        ]

    def get_supervisor_data(self, obj):
        if obj.immediate_supervisor:
            return {
                'id': obj.immediate_supervisor.id,
                'employee_code': obj.immediate_supervisor.employee_code,
                'full_name': obj.immediate_supervisor.full_name,
                'position': obj.immediate_supervisor.position
            }
        return None

    def get_certifications_count(self, obj):
        return obj.certifications.filter(is_valid=True).count()

    def get_certifications_expiring_count(self, obj):
        return obj.certifications_expiring_soon.count()

    def get_medical_records_count(self, obj):
        return obj.medical_records.count()

    def get_supervised_count(self, obj):
        return obj.get_supervised_personnel().count()

    def get_photo_url(self, obj):
        """Devuelve la URL completa de la foto con SAS token"""
        if obj.photo:
            # Generar URL con SAS token para acceso seguro
            return get_photo_url_with_sas(obj.photo)
        return None

    def get_can_approve_level_1(self, obj):
        return obj.can_approve_tokens_level_1()

    def get_can_approve_level_2(self, obj):
        return obj.can_approve_tokens_level_2()

    def get_can_approve_level_3(self, obj):
        return obj.can_approve_tokens_level_3()

    def get_authentication_methods(self, obj):
        """Devuelve los métodos de autenticación disponibles para este usuario"""
        methods = []

        if obj.user:
            # Si tiene usuario, puede autenticarse
            if obj.user.email:
                methods.append({
                    'type': 'email',
                    'value': obj.user.email,
                    'label': 'Correo electrónico',
                    'enabled': True
                })

            if obj.user.username:
                methods.append({
                    'type': 'username',
                    'value': obj.user.username,
                    'label': 'Nombre de usuario',
                    'enabled': True
                })

        return methods

    def validate(self, data):
        """Validaciones personalizadas"""
        # Validar que el supervisor tenga nivel superior
        if 'immediate_supervisor' in data and data['immediate_supervisor']:
            hierarchy_order = {
                'OPERATIVE': 0,
                'SUPERVISOR': 1,
                'AREA_MANAGER': 2,
                'CD_MANAGER': 3
            }
            employee_level = hierarchy_order.get(data.get('hierarchy_level', 'OPERATIVE'), 0)
            supervisor_level = hierarchy_order.get(
                data['immediate_supervisor'].hierarchy_level,
                0
            )
            if supervisor_level <= employee_level:
                raise InvalidSupervisorHierarchy()

        # Validar que department pertenezca al area
        if 'department' in data and data['department']:
            if 'area' in data and data['department'].area != data['area']:
                raise DepartmentNotInArea()

        return data


class PersonnelProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar perfil"""
    emergency_contacts = EmergencyContactSerializer(many=True, required=False)
    has_system_access = serializers.BooleanField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        help_text='Usuario del sistema (opcional)'
    )

    class Meta:
        model = PersonnelProfile
        exclude = ['created_at', 'updated_at', 'created_by']

    def get_fields(self):
        """Override para configurar queryset dinámicamente"""
        fields = super().get_fields()
        from apps.maintenance.models import DistributorCenter

        # Configurar el queryset para distributor_centers dinámicamente
        if 'distributor_centers' in fields:
            fields['distributor_centers'].queryset = DistributorCenter.objects.all()

        # Configurar el queryset para immediate_supervisor dinámicamente
        if 'immediate_supervisor' in fields:
            fields['immediate_supervisor'].queryset = PersonnelProfile.objects.all()

        return fields

    def validate(self, data):
        """Validaciones personalizadas"""
        # Email es requerido SOLO si tiene usuario asignado
        user = data.get('user')
        email = data.get('email', '')

        if user and not email:
            raise EmailRequiredForUser()

        # Validar que el usuario no esté ya asociado a otro perfil (excepto en actualización)
        if user:
            existing_profile = PersonnelProfile.objects.filter(user=user).first()
            if existing_profile and (not self.instance or existing_profile.id != self.instance.id):
                raise UserAlreadyAssigned(
                    f'Este usuario ya tiene un perfil asignado (Empleado: {existing_profile.employee_code})'
                )

        # Validar que el supervisor tenga nivel superior
        if 'immediate_supervisor' in data and data['immediate_supervisor']:
            hierarchy_order = {
                'OPERATIVE': 0,
                'SUPERVISOR': 1,
                'AREA_MANAGER': 2,
                'CD_MANAGER': 3
            }
            employee_level = hierarchy_order.get(data.get('hierarchy_level', 'OPERATIVE'), 0)
            supervisor_level = hierarchy_order.get(
                data['immediate_supervisor'].hierarchy_level,
                0
            )
            if supervisor_level <= employee_level:
                raise InvalidSupervisorHierarchy(
                    f'El supervisor debe tener un nivel jerárquico superior. El empleado es {data.get("hierarchy_level", "OPERATIVE")} y el supervisor es {data["immediate_supervisor"].hierarchy_level}'
                )

        # Validar que department pertenezca al area
        if 'department' in data and data['department']:
            if 'area' in data and data['department'].area != data['area']:
                raise DepartmentNotInArea()

        return data

    def create(self, validated_data):
        emergency_contacts_data = validated_data.pop('emergency_contacts', [])
        distributor_centers_data = validated_data.pop('distributor_centers', [])

        personnel = PersonnelProfile.objects.create(**validated_data)

        # Asignar centros de distribución
        if distributor_centers_data:
            personnel.distributor_centers.set(distributor_centers_data)

        # Crear contactos de emergencia
        for contact_data in emergency_contacts_data:
            EmergencyContact.objects.create(personnel=personnel, **contact_data)

        return personnel

    def update(self, instance, validated_data):
        emergency_contacts_data = validated_data.pop('emergency_contacts', None)
        distributor_centers_data = validated_data.pop('distributor_centers', None)

        # Actualizar perfil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar centros de distribución si se proporcionan
        if distributor_centers_data is not None:
            instance.distributor_centers.set(distributor_centers_data)

        # Actualizar contactos de emergencia si se proporcionan
        if emergency_contacts_data is not None:
            # Eliminar contactos existentes
            instance.emergency_contacts.all().delete()
            # Crear nuevos
            for contact_data in emergency_contacts_data:
                EmergencyContact.objects.create(personnel=instance, **contact_data)

        return instance
