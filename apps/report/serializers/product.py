from rest_framework import serializers

from apps.tracker.models import TrackerDetailProductModel


class TrackerDetailProductSerializer(serializers.Serializer):
    expiration_date = serializers.DateField()
    tracker_detail_product_name = serializers.CharField()
    total_quantity = serializers.IntegerField()