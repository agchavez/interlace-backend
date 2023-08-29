# Rest_framework
from rest_framework import serializers

# Models
from apps.user.models import UserModel
from apps.maintenance.models.centro_distribucion import CentroDistribucion
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
class UserSerializer(serializers.ModelSerializer):
    list_groups = serializers.SerializerMethodField()
    list_permissions = serializers.SerializerMethodField()
    # centro de distribucion un id
    centro_distribucion = serializers.PrimaryKeyRelatedField(
        queryset=CentroDistribucion.objects.all(),
        required=False,
        allow_null=True
    )
    centro_distribucion_name = serializers.ReadOnlyField(source='centro_distribucion.nombre')


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

