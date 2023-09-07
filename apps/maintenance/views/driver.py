from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import DriverModel

# Serializers
from ..serializer import DriverModelSerializer


class DriverFilter(django_filters.FilterSet):
    class Meta:
        model = DriverModel
        fields = {
            'id': ['exact'],
        }


class DriverModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin
                            , viewsets.GenericViewSet):
     queryset = DriverModel.objects.all()
     serializer_class = DriverModelSerializer
     filter_backends = [filters.SearchFilter, DjangoFilterBackend]
     search_fields = ('first_name', 'last_name')
     filterset_class = DriverFilter
