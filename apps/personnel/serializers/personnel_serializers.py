"""
Serializers para modelos de personal
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models.personnel import PersonnelProfile, EmergencyContact
from ..models.organization import Area, Department
from apps.core.azure_utils import get_photo_url_with_sas

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

    class Meta:
        model = Department
        fields = ['id', 'area', 'area_name', 'name', 'code', 'description', 'is_active']
        read_only_fields = ['id']


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
    has_valid_certifications = serializers.BooleanField(read_only=True)
    certifications_count = serializers.SerializerMethodField()
    certifications_expiring_count = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = PersonnelProfile
        fields = [
            'id', 'employee_code', 'user', 'username', 'user_email', 'email',
            'full_name', 'first_name', 'last_name', 'has_system_access',
            'hierarchy_level', 'hierarchy_level_display',
            'position', 'position_type', 'position_type_display',
            'center_name', 'distributor_centers_names', 'area_name', 'department_name',
            'supervisor_name', 'hire_date', 'is_active',
            'has_valid_certifications', 'certifications_count',
            'certifications_expiring_count', 'phone', 'photo_url'
        ]
        read_only_fields = fields

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
                raise serializers.ValidationError({
                    'immediate_supervisor': 'El supervisor debe tener un nivel jerárquico superior'
                })

        # Validar que department pertenezca al area
        if 'department' in data and data['department']:
            if 'area' in data and data['department'].area != data['area']:
                raise serializers.ValidationError({
                    'department': 'El departamento no pertenece al área seleccionada'
                })

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

        return fields

    def validate(self, data):
        """Validaciones personalizadas"""
        # Email es requerido SOLO si tiene usuario asignado
        user = data.get('user')
        email = data.get('email', '')

        if user and not email:
            raise serializers.ValidationError({
                'email': 'El email es requerido para personal con usuario del sistema'
            })

        # Validar que el usuario no esté ya asociado a otro perfil (excepto en actualización)
        if user:
            existing_profile = PersonnelProfile.objects.filter(user=user).first()
            if existing_profile and (not self.instance or existing_profile.id != self.instance.id):
                raise serializers.ValidationError({
                    'user': f'Este usuario ya tiene un perfil asignado (Empleado: {existing_profile.employee_code})'
                })

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
