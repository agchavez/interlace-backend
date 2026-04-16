
from rest_framework import serializers

# Models
from ..models import DistributorCenter, LocationModel, RouteModel, LotModel, DCShiftModel
from .country import CountrySerializer


class DCShiftSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DCShiftModel
        fields = '__all__'


class DistributorCenterSerializer(serializers.ModelSerializer):
    data_country = CountrySerializer(read_only=True, source='country')
    location_distributor_center_code = serializers.ReadOnlyField(source='location_distributor_center.code')
    shifts = DCShiftSerializer(many=True, read_only=True)
    trucks_count = serializers.SerializerMethodField()
    bays_count = serializers.SerializerMethodField()

    class Meta:
        model = DistributorCenter
        fields = '__all__'

    def get_trucks_count(self, obj):
        if hasattr(obj, 'pautas'):
            from apps.truck_cycle.models.catalogs import TruckModel
            return TruckModel.objects.filter(distributor_center=obj, is_active=True).count()
        return 0

    def get_bays_count(self, obj):
        from apps.truck_cycle.models.catalogs import BayModel
        return BayModel.objects.filter(distributor_center=obj, is_active=True).count()

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

