
from rest_framework import serializers

# Models
from ..models import DistributorCenter, LocationModel, RouteModel, LotModel
from .country import CountrySerializer

class DistributorCenterSerializer(serializers.ModelSerializer):
    data_country = CountrySerializer(read_only=True, source='country')
    location_distributor_center_code = serializers.ReadOnlyField(source='location_distributor_center.code')
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

class LotModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotModel
        fields = '__all__'

