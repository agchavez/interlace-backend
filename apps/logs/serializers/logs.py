
from rest_framework import serializers

from ..models import LogActionModel, LogControlModel


class LogActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogActionModel
        fields = '__all__'
        read_only_fields = ['id']


class LogControlSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    person_name = serializers.SerializerMethodField('get_user_person_name')
    email = serializers.ReadOnlyField(source='user.email')
    action = LogActionSerializer(read_only=True)

    def get_user_person_name(self, obj):
        person_name = obj.user.first_name + " " + obj.user.last_name
        return person_name

    class Meta:
        model = LogControlModel
        fields = '__all__'
        read_only_fields = ['id']