
# rest_framework
from rest_framework import serializers

# Models
from apps.tracker.models import TypeDetailOutputModel, TrackerDetailOutputModel
from apps.maintenance.serializer import ProductModelSerializer
class TypeDetailOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeDetailOutputModel
        fields = '__all__'


class TrackerDetailOutputSerializer(serializers.ModelSerializer):
    product_data = ProductModelSerializer(source='product', read_only=True)
    class Meta:
        model = TrackerDetailOutputModel
        fields = '__all__'

    def validate(self, attrs):
        # No se puede agregar productos de tarcker ya completado
        if attrs['tracker'].status == 'COMPLETADO':
            raise serializers.ValidationError(
                {
                    "mensage": "No se puede agregar productos de tracker ya completado",
                    "error_code": "tracker_complete"
                })
        return attrs
