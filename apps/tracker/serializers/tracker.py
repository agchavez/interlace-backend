# rest_framework
from django.db.models import Sum
from rest_framework import serializers

# Models
from apps.tracker.models import TrackerModel, TrackerDetailModel, TrackerDetailProductModel

from apps.tracker.exceptions.tracker import TrackerCompleted, TransporterRequired, TrailerRequired, PalletsExceeded, \
    TrailerInUse
from apps.maintenance.serializer import TrailerModelSerializer, TransporterModelSerializer, DistributorCenterSerializer, \
    ProductModelSerializer


class TrackerDetailProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerDetailProductModel
        fields = '__all__'

    # la suma de las cantidades de los productos no puede ser mayor a la cantidad del tracker

    def validate(self, data):
        quantity = data.get('quantity')
        sum_quantity = TrackerDetailProductModel.objects.filter(tracker_detail=data.get('tracker_detail')).aggregate(
            Sum('quantity'))
        if sum_quantity.get('quantity__sum') and sum_quantity.get('quantity__sum') + quantity > data.get(
                'tracker_detail').quantity:
            raise PalletsExceeded()
        return data


# Modelo para los detalles de los trackers

class TrackerDetailModelSerializer(serializers.ModelSerializer):
    tracker_product_detail = TrackerDetailProductModelSerializer(many=True, read_only=True)
    product_data = ProductModelSerializer(source='product', read_only=True)

    class Meta:
        model = TrackerDetailModel
        fields = '__all__'


class TrackerSerializer(serializers.ModelSerializer):
    tariler_data = serializers.SerializerMethodField('get_tariler')
    transporter_data = serializers.SerializerMethodField('get_transporter')
    distributor_center_data = DistributorCenterSerializer(source='distributor_center', read_only=True)
    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    tracker_detail = TrackerDetailModelSerializer(many=True, read_only=True)

    def get_tariler(self, obj):
        return TrailerModelSerializer(obj.trailer).data

    def get_transporter(self, obj):
        return TransporterModelSerializer(obj.transporter).data

    class Meta:
        model = TrackerModel
        fields = '__all__'

    def validate(self, data):
        # solo se pueden actualizar si el estado es PENDING
        if self.instance and self.instance.status == 'COMPLETE':
            raise TrackerCompleted()

        # Obligatorio solicitar el trailer y el transportista, solo si es un POST
        if not data.get('trailer') and not self.instance:
            raise TrailerRequired()
        if not data.get('transporter') and not self.instance:
            raise TransporterRequired()

        # No se puede registrar un tracker con un trailer que ya este en uso (PENDING)
        if data.get('trailer') and not self.instance:
            if TrackerModel.objects.filter(trailer=data.get('trailer'), status='PENDING').exists():
                raise TrailerInUse()
        return data

    def create(self, validated_data):
        return TrackerModel.objects.create(**validated_data)
