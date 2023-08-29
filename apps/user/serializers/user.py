# Rest_framework
import json

from rest_framework import serializers
from django.contrib.auth.hashers import make_password

# Models
from apps.user.models import UserModel

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

