from rest_framework import serializers

# Models
from ..models import PeriodModel
from .centro_distribucion import DistributorCenterSerializer

class PeriodModelSerializer(serializers.ModelSerializer):
    distributor_center_data = DistributorCenterSerializer(read_only=True, source='distributor_center')
    product_name = serializers.ReadOnlyField(source='product.name')
    class Meta:
        model = PeriodModel
        fields = '__all__'