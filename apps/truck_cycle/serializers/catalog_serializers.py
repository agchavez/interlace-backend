"""
Serializers para catálogos del ciclo del camión
"""
from rest_framework import serializers
from apps.truck_cycle.models.catalogs import (
    TruckModel,
    ProductCatalogModel,
    BayModel,
    KPITargetModel,
)


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckModel
        fields = '__all__'


class ProductCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCatalogModel
        fields = '__all__'


class BaySerializer(serializers.ModelSerializer):
    class Meta:
        model = BayModel
        fields = '__all__'


class KPITargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPITargetModel
        fields = '__all__'
