from rest_framework import serializers

# Models
from ..models import ProductModel, OutputTypeModel


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'


class OutputTypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutputTypeModel
        fields = '__all__'


