
from rest_framework import serializers

# Models
from ..models import CentroDistribucion


class CentroDistribucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroDistribucion
        fields = '__all__'