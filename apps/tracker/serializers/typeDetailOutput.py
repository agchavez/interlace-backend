# rest_framework
from rest_framework import serializers

# Models
from apps.tracker.models import TypeDetailOutputModel


class TypeDetailOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeDetailOutputModel
        fields = '__all__'
