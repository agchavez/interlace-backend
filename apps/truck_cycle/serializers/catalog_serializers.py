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
        extra_kwargs = {'distributor_center': {'required': False}}


class ProductCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCatalogModel
        fields = '__all__'
        extra_kwargs = {'distributor_center': {'required': False}}


class BaySerializer(serializers.ModelSerializer):
    class Meta:
        model = BayModel
        fields = '__all__'
        extra_kwargs = {'distributor_center': {'required': False}}


class KPITargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPITargetModel
        fields = '__all__'
        extra_kwargs = {'distributor_center': {'required': False}}
