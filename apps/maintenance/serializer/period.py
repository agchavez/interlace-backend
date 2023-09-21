from rest_framework import serializers

# Models
from ..models import PeriodModel

class PeriodModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodModel
        fields = '__all__'