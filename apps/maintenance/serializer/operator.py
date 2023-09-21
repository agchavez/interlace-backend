from rest_framework import serializers

# Models
from ..models import OperatorModel


class OperatorModelSerializer(serializers.ModelSerializer):
    distributor_center_name = serializers.ReadOnlyField(source='distributor_center.name')
    class Meta:
        model = OperatorModel
        fields = '__all__'



