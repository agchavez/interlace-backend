# Rest_framework
from rest_framework import serializers

# Models
from apps.user.models import UserModel, DetailGroup
from apps.maintenance.models.distributor_center import DistributorCenter
# Grupos y permisos
from django.contrib.auth.models import Group, Permission, ContentType, UserManager

# Log de administrador
from django.contrib.admin.models import LogEntry


# Serializers (User)
class UserDJSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'


# Serializers (UserModel)
ACTIVE_DISTRIBUTION_CENTERS = [1, 2]  # CD LA GRANJA (1), CD COMAYAGUA (2)

class UserSerializer(serializers.ModelSerializer):
    list_groups = serializers.SerializerMethodField()
    list_permissions = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    # centro de distribucion un id
    centro_distribucion = serializers.PrimaryKeyRelatedField(
        queryset=DistributorCenter.objects.all(),
        required=False,
        allow_null=True
    )
    centro_distribucion_name = serializers.SerializerMethodField("get_centro_distribucion")
    photo_url = serializers.SerializerMethodField()
    personnel_profile_id = serializers.SerializerMethodField()
    distributions_centers = serializers.SerializerMethodField()

    def get_personnel_profile_id(self, obj):
        """Obtiene el ID del perfil de personal si existe"""
        if hasattr(obj, 'personnel_profile') and obj.personnel_profile:
            return obj.personnel_profile.id
        return None

    def get_centro_distribucion(self, obj):
        if obj.centro_distribucion is None:
            return None
        if hasattr(obj.centro_distribucion,
                   'location_distributor_center') and obj.centro_distribucion.location_distributor_center is not None:
            return obj.centro_distribucion.location_distributor_center.code + " - " + obj.centro_distribucion.name
        else:
            return obj.centro_distribucion.name

    def get_photo_url(self, obj):
        """Obtiene la URL de la foto del perfil de personal si existe"""
        if hasattr(obj, 'personnel_profile') and obj.personnel_profile:
            if obj.personnel_profile.photo:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.personnel_profile.photo.url)
                return obj.personnel_profile.photo.url
        return None

    def get_distributions_centers(self, obj):
        return list(
            obj.distributions_centers
            .filter(id__in=ACTIVE_DISTRIBUTION_CENTERS)
            .values_list('id', flat=True)
        )

    # validacion al registrar que si hay un grupo seleccionado, verificar si requiere acceso o no
    def validate(self, data):
        if 'groups' in data:
            for group in data['groups']:
                group = Group.objects.get(id=group.id)
                if group.detail_group.requiered_access and not data['centro_distribucion']:
                    raise serializers.ValidationError(
                        {
                            "mensage": "El grupo seleccionado requiere que se le asigne un centro de distribucion",
                            "error_code": "required_access_group"
                        })
        # Si el grupo es SUPERADMIN, se agrega el is_staff en true de lo contrario en false
        if 'groups' in data:
            for group in data['groups']:
                if group.name == 'SUPERADMIN':
                    data['is_staff'] = True
                    break
                else:
                    data['is_staff'] = False
        # en los centros de distribucion asociados tiene que existir el centro de distribucion
        if 'centro_distribucion' in data and 'distributions_centers' in data:
            distributions_centers = data['distributions_centers']
            # en el arreglo de centros de distribucion asociados tiene que existir el centro de distribucion
            if data['centro_distribucion'] not in distributions_centers:
                # agregar el centro de distribucion al arreglo de centros de distribucion asociados
                distributions_centers.append(data['centro_distribucion'])

        return data
    @staticmethod
    def get_list_groups(obj):
        return obj.groups.values_list('name', flat=True)

    @staticmethod
    def get_list_permissions(obj):
        return obj.get_all_permissions()
    # Omiti el campo password para que no se muestre en el response
    class Meta:
        model = UserModel
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}




# Serializer para validar cada fila del Excel de carga masiva
class BulkUploadRowSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=60)
    last_name = serializers.CharField(max_length=60)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    password = serializers.CharField(min_length=8, write_only=True)
    employee_number = serializers.IntegerField(required=False, allow_null=True, default=None)
    group = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_email(self, value):
        if UserModel.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("El email ya está registrado.")
        return value.lower()

    def validate_username(self, value):
        if value and UserModel.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("El username ya existe.")
        return value

    def validate_employee_number(self, value):
        if value and UserModel.objects.filter(employee_number=value).exists():
            raise serializers.ValidationError("El número de empleado ya existe.")
        return value


# Serializers (ContentType)
class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'


# Serializers (Permission)
class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer()

    class Meta:
        model = Permission
        fields = '__all__'


# Serializers (Group)
class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = '__all__'


# Serializers (DetailGroup)
class DetailGroupSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = DetailGroup
        fields = '__all__'


# Serializers (LogEntry)
class LogEntrySerializer(serializers.ModelSerializer):
    user = UserDJSerializer()
    content_type = ContentTypeSerializer()
    change_message_formatted = serializers.SerializerMethodField()
    type_action = serializers.SerializerMethodField()

    @staticmethod
    def get_type_action(obj):
        type_log = ""
        if obj.action_flag == 1:
            type_log = "add"
        elif obj.action_flag == 2:
            type_log = "update"
        elif obj.action_flag == 3:
            type_log = "delete"
        model = obj.content_type.model
        return type_log + "-" + model

    @staticmethod
    def get_change_message_formatted(obj):
        return obj.get_change_message()

    class Meta:
        model = LogEntry
        fields = '__all__'

