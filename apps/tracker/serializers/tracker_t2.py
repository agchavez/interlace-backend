from rest_framework import serializers

from ..models import TrackerOutputT2Model, OutputDetailT2Model, OutputT2Model


class TrackerOutputT2Serializer(serializers.ModelSerializer):
    class Meta:
        model = TrackerOutputT2Model
        fields = '__all__'


class OutputDetailT2Serializer(serializers.ModelSerializer):
    tracker_output_t2 = TrackerOutputT2Serializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sap_code = serializers.CharField(source='product.sap_code', read_only=True)
    class Meta:
        model = OutputDetailT2Model
        fields = '__all__'


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


