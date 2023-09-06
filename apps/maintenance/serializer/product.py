from rest_framework import serializers

# Models
from ..models import ProductModel


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'
