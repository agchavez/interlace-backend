
from rest_framework import serializers

# Models
from ..models import DistributorCenter, LocationModel, RouteModel


class DistributorCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributorCenter
        fields = '__all__'

class LocationModelSerializer(serializers.ModelSerializer):
    distributor_center_name = serializers.ReadOnlyField(source='distributor_center.name')
    class Meta:
        model = LocationModel
        fields = '__all__'


class RouteModelSerializer(serializers.ModelSerializer):
    distributor_center_name = serializers.ReadOnlyField(source='distributor_center.name')
    location_name = serializers.ReadOnlyField(source='location.name')
    class Meta:
        model = RouteModel
        fields = '__all__'
