from rest_framework import serializers

# Models
from ..models import DriverModel


class DriverModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverModel
        fields = '__all__'


