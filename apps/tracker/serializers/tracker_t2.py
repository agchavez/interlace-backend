from rest_framework import serializers

from ..models import TrackerOutputT2Model, OutputDetailT2Model, OutputT2Model

class OutputDetailT2Serializer(serializers.ModelSerializer):
    class Meta:
        model = OutputDetailT2Model
        fields = '__all__'

class OutputT2Serializer(serializers.ModelSerializer):
    output_detail_t2 = OutputDetailT2Serializer(many=True)
    class Meta:
        model = OutputT2Model
        fields = '__all__'

    def create(self, validated_data):
        output_detail_t2 = validated_data.pop('output_detail_t2')
        output = OutputT2Model.objects.create(**validated_data)
        for output_detail_t2 in output_detail_t2:
            OutputDetailT2Model.objects.create(output=output, **output_detail_t2)
        return output


class TrackerOutputT2Serializer(serializers.ModelSerializer):
    output_data = OutputT2Serializer(source='output', read_only=True)
    class Meta:
        model = TrackerOutputT2Model
        fields = '__all__'

    def create(self, validated_data):
        output = validated_data.pop('output')
        tracker_output_t2 = TrackerOutputT2Model.objects.create(**validated_data)
        OutputT2Model.objects.create(tracker_output_t2=tracker_output_t2, **output)
        return tracker_output_t2

    