from rest_framework import serializers

# Models
from ..models import TransporterModel, TrailerModel

class TransporterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransporterModel
        fields = '__all__'


class TrailerModelSerializer(serializers.ModelSerializer):
    transporter = TransporterModelSerializer()
    class Meta:
        model = TrailerModel
        fields = '__all__'


