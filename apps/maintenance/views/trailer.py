from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import TrailerModel, TransporterModel

# Serializers
from ..serializer import TrailerModelSerializer, TransporterModelSerializer


class TrailerFilter(django_filters.FilterSet):
    class Meta:
        model = TrailerModel
        fields = {
            'transporter': ['exact'],
            'id': ['exact'],
        }


class TrailerModelViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = TrailerModel.objects.all()
    serializer_class = TrailerModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('code',)
    filterset_class = TrailerFilter


class TransporterModelViewSet(mixins.ListModelMixin
    , viewsets.GenericViewSet):
    queryset = TransporterModel.objects.all()
    serializer_class = TransporterModelSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('tractor', 'code', 'name', 'head')
