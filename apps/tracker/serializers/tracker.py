# rest_framework
from django.db.models import Sum, Q
from rest_framework import serializers

# Models
from apps.tracker.models import TrackerModel, TrackerDetailModel, TrackerDetailProductModel

from apps.tracker.exceptions.tracker import TrackerCompleted, TransporterRequired, TrailerRequired, PalletsExceeded, \
    TrailerInUse, TrackerCompletedDetail, TrackerCompletedDetailProduct, InputDocumentNumberIsNotNumber, \
    InputDocumentNumberRegistered

from apps.maintenance.serializer import TrailerModelSerializer, TransporterModelSerializer, DistributorCenterSerializer, \
    ProductModelSerializer, LocationModelSerializer

from .typeDetailOutput import TrackerDetailOutputSerializer


class TrackerDetailProductModelSerializer(serializers.ModelSerializer):
    tracker_id = serializers.ReadOnlyField(source='tracker_detail.tracker.id')
    tracker_detail_id = serializers.ReadOnlyField(source='tracker_detail.id')
    product_name = serializers.ReadOnlyField(source='tracker_detail.product.name')
    product_sap_code = serializers.ReadOnlyField(source='tracker_detail.product.sap_code')

    class Meta:
        model = TrackerDetailProductModel
        fields = '__all__'

    # la suma de las cantidades de los productos no puede ser mayor a la cantidad del tracker

    def validate(self, data):
        quantity = data.get('quantity')
        # Omitir la instancia actual en caso de que sea una actualización y si no hay mas registros el valor es 0
        if self.instance:
            sum_quantity = TrackerDetailProductModel.objects.filter(tracker_detail=data.get('tracker_detail')).exclude(
                id=self.instance.id).aggregate(Sum('quantity'))
            if sum_quantity.get('quantity__sum') is None:
                sum_quantity = {'quantity__sum': 0}

        else:
            sum_quantity = TrackerDetailProductModel.objects.filter(tracker_detail=data.get('tracker_detail')).aggregate(
                Sum('quantity'))
            if sum_quantity.get('quantity__sum') is None:
                sum_quantity = {'quantity__sum': 0}
        value = sum_quantity.get('quantity__sum')
        if (value + quantity) > data.get(
                'tracker_detail').quantity:
            raise PalletsExceeded()
        tracker_detail = TrackerDetailModel.objects.get(id=data.get('tracker_detail').id)
        if tracker_detail.tracker.status == 'COMPLETE':
            raise TrackerCompletedDetailProduct()
        return data


# Modelo para los detalles de los trackers

class TrackerDetailModelSerializer(serializers.ModelSerializer):
    tracker_product_detail = TrackerDetailProductModelSerializer(many=True, read_only=True)
    product_data = ProductModelSerializer(source='product', read_only=True)

    def validate(self, attrs):
        tracker = attrs.get('tracker')
        if tracker.status == 'COMPLETE':
            raise TrackerCompletedDetail()
        return attrs

    class Meta:
        model = TrackerDetailModel
        fields = '__all__'


class TrackerSerializer(serializers.ModelSerializer):
    tariler_data = serializers.SerializerMethodField('get_tariler')
    transporter_data = serializers.SerializerMethodField('get_transporter')
    distributor_center_data = DistributorCenterSerializer(source='distributor_center', read_only=True)
    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    tracker_detail = TrackerDetailModelSerializer(many=True, read_only=True)
    location_data = LocationModelSerializer(source = 'origin_location', read_only=True)
    tracker_detail_output = TrackerDetailOutputSerializer(many=True, read_only=True)
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
        #if data.get('trailer') and not self.instance:
            #if TrackerModel.objects.filter(trailer=data.get('trailer'), distributor_center=data.get('distributor_center')).filter(Q(status='PENDING') | Q(status='EDITED')).exists():
                #raise TrailerInUse()

        if self.instance and 'status' in data and data['status'] == "COMPLETE":
            raise serializers.ValidationError("No se puede cambiar el estado del tracker")
        # tiempo final no puede ser menor al tiempo inicial y calcular la diferencia de tiempo
        if data.get('output_date') and data.get('input_date') and data.get('output_date') < data.get('input_date') and self.instance:
            raise serializers.ValidationError("El tiempo final no puede ser menor al tiempo inicial")
        return data

    def create(self, validated_data):
        return TrackerModel.objects.create(**validated_data)
