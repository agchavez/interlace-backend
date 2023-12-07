from django.db.models import Sum
from rest_framework import serializers

from ..exceptions.tracker_t2 import QuantityExceededOut, QuantityMajorZero, TrackerDetailExist, \
    TrackerDetailProductRequired, QuantityRequired, QuantitySumExceeded
from ..models import TrackerOutputT2Model, OutputDetailT2Model, OutputT2Model, TrackerDetailProductModel
from ...maintenance.serializer import DistributorCenterSerializer
from ...order.exceptions.order_detail import CustomAPIException, QuantityExceeded


class TrackerOutputT2Serializer(serializers.ModelSerializer):

    def validate(self, data):
        if data['quantity'] <= 0:
            raise QuantityMajorZero()

        # No pueden existir dos tracker_output_t2 con el mismo tracker_detail
        # if not self.instance:
        #     if TrackerOutputT2Model.objects.filter(tracker_detail=data['tracker_detail']).exists():
        #         raise TrackerDetailExist()

        # la cantiadad no puede se mayor a la cantidad disponible en el tracker
        if data['quantity'] > data['tracker_detail'].available_quantity:
            raise QuantityExceeded()

        # suma de todos los tracker_output_t2 con el mismo output_detail
        if not self.instance:
            sum_quantity = TrackerOutputT2Model.objects.filter(output_detail=data['output_detail']).aggregate(total=Sum('quantity'))['total']
        else:
            sum_quantity = TrackerOutputT2Model.objects.filter(output_detail=data['output_detail']).exclude(id=self.instance.id).aggregate(total=Sum('quantity'))['total']
        sum_quantity = sum_quantity if sum_quantity else 0
        sum_quantity = sum_quantity + data['quantity'] if self.instance else sum_quantity
        if sum_quantity > data['output_detail'].quantity:
            raise QuantityExceededOut()
        return data

    def create(self, validated_data):

        value = TrackerOutputT2Model.objects.create(**validated_data)
        value.save()

        # si la suma de todos los tracker_output_t2 con el mismo output_detail es igual a la cantidad de la salida, cambiar el status a CHECKED
        sum_quantity = TrackerOutputT2Model.objects.filter(output_detail=validated_data['output_detail']).aggregate(total=Sum('quantity'))['total']
        if sum_quantity == validated_data['output_detail'].quantity:
            validated_data['output_detail'].status = 'CHECKED'
            validated_data['output_detail'].save()
        return value

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()

        # si la suma de todos los tracker_output_t2 con el mismo output_detail es igual a la cantidad de la salida, cambiar el status a CHECKED
        sum_quantity = TrackerOutputT2Model.objects.filter(output_detail=instance.output_detail).aggregate(total=Sum('quantity'))['total']
        if sum_quantity == instance.output_detail.quantity:
            instance.output_detail.status = 'CHECKED'
            instance.output_detail.save()
        else:
            instance.output_detail.status = 'CREATED'
            instance.output_detail.save()
        return instance

    class Meta:
        model = TrackerOutputT2Model
        fields = '__all__'


class OutputDetailT2Serializer(serializers.ModelSerializer):
    tracker_output_t2 = TrackerOutputT2Serializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sap_code = serializers.CharField(source='product.sap_code', read_only=True)
    details = serializers.SerializerMethodField('get_details')

    def get_details(self, obj):
        details = []
        total_quantity = 0

        for item in obj.output_detail_tracker_t2.all():
            expiration_date = item.tracker_detail.expiration_date
            quantity = item.quantity
            total_quantity += quantity

            # Buscar si ya existe un detalle con la misma fecha de vencimiento
            existing_detail = next((detail for detail in details if detail['expiration_date'] == expiration_date), None)

            if existing_detail:
                # Si ya existe, agregar la cantidad al de   talle existente
                existing_detail['quantity'] += quantity
                existing_detail['details'].append(TrackerOutputT2Serializer(item).data)
            else:
                # Si no existe, agregar un nuevo detalle
                details.append({
                    'expiration_date': expiration_date,
                    'quantity': quantity,
                    'details': [TrackerOutputT2Serializer(item).data]
                })

        return {
            'details': details,
            'total_quantity': total_quantity
        }

    class Meta:
        model = OutputDetailT2Model
        fields = '__all__'
        # create_at no mostrar en el serializer

# Serializer de carga masiva de salida de productos T2
class OutputTrackerT2MassiveSerializer(serializers.Serializer):
    list = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(max_length=100)
        )
    )
    list_delete = serializers.ListField(
        child=serializers.IntegerField()
    )
    quantity = serializers.IntegerField(allow_null=True, required=False)

    # validar que los lista de numeros sean instancias de TrackerOutputT2Model
    def validate_list_delete(self, value):
        for item in value:
            try:
                TrackerOutputT2Model.objects.get(id=item)
            except TrackerOutputT2Model.DoesNotExist:
                raise CustomAPIException(
                    detail=f"No existe registro de tracker con el id: {item}.",
                    code='order_not_completed',
                )
        return value

    def validate_list(self, value):
        # validar que no se repitan los tracker_detail_product
        tracker_detail_product_list = []
        sum_quantity = 0
        output_detail = self.context.get('output_detail')
        for item in value:
            # Verificar que 'tracker_detail_product' esté presente
            if 'tracker_detail_product' not in item:
                raise TrackerDetailProductRequired()

            # Verificar que 'quantity' esté presente
            if 'quantity' not in item:
                raise QuantityRequired()
            else:
                item['quantity'] = int(item['quantity'])

            sum_quantity = sum_quantity + item['quantity']
            tracker_detail_product_id = item['tracker_detail_product']
            if tracker_detail_product_id in tracker_detail_product_list:
                raise serializers.ValidationError(f"El tracker_detail_product {tracker_detail_product_id} está repetido.")
            tracker_detail_product_list.append(tracker_detail_product_id)


            # Verificar que 'tracker_detail_product' existe en TrackerDetailProductModel
            tracker_detail_product_id = item['tracker_detail_product']
            try:
                value_trk = TrackerDetailProductModel.objects.get(id=tracker_detail_product_id)

                # la cantidad no supere la cantidad disponible en el tracker
                if item['quantity'] > value_trk.available_quantity:
                    raise CustomAPIException(
                        detail=f"La cantidad no puede ser mayor a la cantidad disponible en el tracker {tracker_detail_product_id}",
                        code='quantity_exceeded_detail',
                    )
            except TrackerDetailProductModel.DoesNotExist:
                raise CustomAPIException(
                    detail=f"No existe registro de tracker con el id: {tracker_detail_product_id}.",
                    code='order_not_completed',
                )
            # validar que no exista el mismo tracker_detail_product ya registrado en la base de datos para el mismo output_detail
                # if TrackerOutputT2Model.objects.filter(tracker_detail_id=tracker_detail_product_id, output_detail=output_detail).exists() and not
                #     raise CustomAPIException(
                #         detail=f"El detalle de producto con id: {tracker_detail_product_id} ya existe para esta salida.",
                #         code='tracker_detail_product_exist',
                #     )
        # la suma de las cantidades no puede ser mayor a la cantidad de la salida
        if sum_quantity > output_detail.quantity:
            raise QuantitySumExceeded()

        return value


# serializaer solo para visualizar la informacion principal de la salida
class OutputT2ListSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    count_details = serializers.SerializerMethodField()
    user_authorizer_name = serializers.SerializerMethodField()
    user_check_name = serializers.SerializerMethodField()
    user_applied_name = serializers.SerializerMethodField()
    distributor_center_data = DistributorCenterSerializer(source='distributor_center', read_only=True)
    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_user_authorizer_name(self, obj):
        return obj.user_authorizer.get_full_name() if obj.user_authorizer else None

    def get_user_applied_name(self, obj):
        return obj.user_applied.get_full_name() if obj.user_applied else None

    def get_user_check_name(self, obj):
        return obj.user_check.get_full_name() if obj.user_check else None

    def get_count_details(self, obj):
        return obj.output_detail_t2.count()
    class Meta:
        model = OutputT2Model
        fields = '__all__'

class OutputT2Serializer(serializers.ModelSerializer):
    output_detail_t2 = OutputDetailT2Serializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    user_authorizer_name = serializers.SerializerMethodField()
    user_check_name = serializers.SerializerMethodField()
    user_applied_name = serializers.SerializerMethodField()
    distributor_center_data = DistributorCenterSerializer(source='distributor_center', read_only=True)
    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_user_authorizer_name(self, obj):
        return obj.user_authorizer.get_full_name() if obj.user_authorizer else None

    def get_user_applied_name(self, obj):
        return obj.user_applied.get_full_name() if obj.user_applied else None

    def get_user_check_name(self, obj):
        return obj.user_check.get_full_name() if obj.user_check else None

    def validate(self, data):
        if self.instance:
            if self.instance.status == 'APPLIED':
                raise CustomAPIException(
                    detail=f"La salida ya fue aplicada, no se puede modificar.",
                    code='output_applied',
                )
            # Solo se permiten estados CHECKED, REJECTED y AUTHORIZED
            if data['status'] not in ['CHECKED', 'REJECTED', 'AUTHORIZED']:
                raise CustomAPIException(
                    detail=f"El estado no puede ser modificado.",
                    code='output_status_not_allowed',
                )
            # Si es CHECKED el estado anterior debe ser CREATED o REJECTED
            if data['status'] == 'CHECKED':
                if self.instance.status not in ['CREATED', 'REJECTED']:
                    raise CustomAPIException(
                        detail=f"Ya no se puede cambiar el estado a revisado.",
                        code='output_status_created',
                    )
            # Si es AUTHORIZED el estado anterior debe ser CHECKED
            if data['status'] == 'AUTHORIZED':
                if self.instance.status != 'CHECKED':
                    raise CustomAPIException(
                        detail=f"Ya no se puede cambiar el estado a autorizado.",
                        code='output_status_checked',
                    )
            # Si es REJECTED el estado anterior debe ser CHECKED
            if data['status'] == 'REJECTED':
                if self.instance.status != 'CHECKED':
                    raise CustomAPIException(
                        detail=f"Ya no se puede cambiar el estado a rechazado.",
                        code='output_status_checked',
                    )

            # Si es REJECTED verificar que almenos un detalle tenga el status REJECTED
            if data['status'] == 'REJECTED':
                if not self.instance.output_detail_t2.filter(status='REJECTED').exists():
                    raise CustomAPIException(
                        detail=f"Debe existir almenos un detalle rechazado.",
                        code='output_status_rejected',
                    )
        return data

    def update(self, instance, validated_data):
        user = self.context['request'].user
        # Si es UN status CHECKED, cambiar todos los status de los tracker_output_t2 a CHECKED
        if validated_data['status'] == 'CHECKED':
            instance.user_check = user
            if instance.status == 'REJECTED':
                OutputDetailT2Model.objects.filter(output=instance, status='REJECTED').update(status='CREATED')
            else:
                OutputDetailT2Model.objects.filter(output=instance).update(status='CHECKED')
        # Si es UN status AUTHORIZED, cambiar todos los status de los tracker_output_t2 a AUTHORIZED
        if validated_data['status'] == 'AUTHORIZED':
            instance.user_authorizer = user
            OutputDetailT2Model.objects.filter(output=instance).update(status='AUTHORIZED')
        # Actualizar el status de la salida
        instance.status = validated_data['status']
        instance.save()
        return instance

    class Meta:
        model = OutputT2Model
        fields = '__all__'


