from django.db.models import Sum
from rest_framework import serializers

from ..models import TrackerOutputT2Model, OutputDetailT2Model, OutputT2Model, TrackerDetailProductModel

class TrackerOutputT2Serializer(serializers.ModelSerializer):

    def validate(self, data):
        if data['quantity'] <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor a 0')

        # No pueden existir dos tracker_output_t2 con el mismo tracker_detail
        if not self.instance:
            if TrackerOutputT2Model.objects.filter(tracker_detail=data['tracker_detail']).exists():
                raise serializers.ValidationError('Ya existe un registro con el mismo tracker_detail')

        # la cantiadad no puede se mayor a la cantidad disponible en el tracker
        if data['quantity'] > data['tracker_detail'].available_quantity:
            raise serializers.ValidationError('La cantidad no puede ser mayor a la cantidad disponible en el tracker')

        # suma de todos los tracker_output_t2 con el mismo output_detail
        if not self.instance:
            sum_quantity = TrackerOutputT2Model.objects.filter(output_detail=data['output_detail']).aggregate(total=Sum('quantity'))['total']
        else:
            sum_quantity = TrackerOutputT2Model.objects.filter(output_detail=data['output_detail']).exclude(id=self.instance.id).aggregate(total=Sum('quantity'))['total']
        sum_quantity = sum_quantity if sum_quantity else 0
        sum_quantity = sum_quantity + data['quantity'] if self.instance else sum_quantity
        if sum_quantity > data['output_detail'].quantity:
            raise serializers.ValidationError('La cantidad no puede ser mayor a la cantidad de la salida')
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
        # listar detalles de salida agrupados por fecha de vencimiento y con la suma de cada grupo de por fecha
        details = []
        for item in obj.output_detail_tracker_t2.all():
            expiration_date = item.tracker_detail.expiration_date
            quantity = item.quantity
            if not expiration_date in details:
                details.append({
                    'expiration_date': expiration_date,
                    'quantity': quantity,
                    'details': [TrackerOutputT2Serializer(item).data]
                })
            else:
                for detail in details:
                    if detail['expiration_date'] == expiration_date:
                        detail['quantity'] = detail['quantity'] + quantity
                        detail['details'].append(TrackerOutputT2Serializer(item).data)
        return details

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

    # validar que los lista de numeros sean instancias de TrackerOutputT2Model
    def validate_list_delete(self, value):
        for item in value:
            try:
                TrackerOutputT2Model.objects.get(id=item)
            except TrackerOutputT2Model.DoesNotExist:
                raise serializers.ValidationError(f"El tracker_output_t2 {item} no existe.")
        return value

    def validate_list(self, value):
        # validar que no se repitan los tracker_detail_product
        tracker_detail_product_list = []
        sum_quantity = 0
        output_detail = self.context.get('output_detail')
        for item in value:
            # Verificar que 'tracker_detail_product' esté presente
            if 'tracker_detail_product' not in item:
                raise serializers.ValidationError("Cada elemento debe tener 'tracker_detail_product'.")


            # Verificar que 'quantity' esté presente
            if 'quantity' not in item:
                raise serializers.ValidationError("Cada elemento debe tener 'quantity'.")
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
                    raise serializers.ValidationError(f"La cantidad no puede ser mayor a la cantidad disponible en el tracker {tracker_detail_product_id}")

            except TrackerDetailProductModel.DoesNotExist:
                raise serializers.ValidationError(f"'tracker_detail_product' {tracker_detail_product_id} no existe.")

            # validar que no exista el mismo tracker_detail_product ya registrado en la base de datos para el mismo output_detail
            if TrackerOutputT2Model.objects.filter(tracker_detail_id=tracker_detail_product_id, output_detail=output_detail).exists():
                raise serializers.ValidationError(f"El tracker_detail_product {tracker_detail_product_id} ya existe para esta salida.")

        # la suma de las cantidades no puede ser mayor a la cantidad de la salida
        if sum_quantity > output_detail.quantity:
            raise serializers.ValidationError(f"La suma de las cantidades no puede ser mayor a la cantidad de la salida.")

        return value


class OutputT2Serializer(serializers.ModelSerializer):
    output_detail_t2 = OutputDetailT2Serializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    user_authorizer_name = serializers.SerializerMethodField()
    user_receiver_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_user_authorizer_name(self, obj):
        return obj.user_authorizer.get_full_name() if obj.user_authorizer else None

    def get_user_receiver_name(self, obj):
        return obj.user_receiver.get_full_name() if obj.user_receiver else None

    class Meta:
        model = OutputT2Model
        fields = '__all__'


