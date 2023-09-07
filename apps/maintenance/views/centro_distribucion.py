
from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import DistributorCenter, LocationModel, RouteModel

# Serializers
from ..serializer import DistributorCenterSerializer, RouteModelSerializer, LocationModelSerializer


class CentroDistribucionFilter(django_filters.FilterSet):
    class Meta:
        model = DistributorCenter
        fields = {
            'country_code': ['exact'],
            'id': ['exact'],
        }

class CentroDistribucionViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin
                                , viewsets.GenericViewSet):
    queryset = DistributorCenter.objects.all()
    serializer_class = DistributorCenterSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name')
    filterset_class = CentroDistribucionFilter
    # Quitar la paginacion
    pagination_class = None

class RouteFilter(django_filters.FilterSet):
    class Meta:
        model = RouteModel
        fields = {
            'distributor_center': ['exact'],
            'location': ['exact'],
            'id': ['exact'],
        }

class RouteModelViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin
                                , viewsets.GenericViewSet):
    queryset = RouteModel.objects.all()
    serializer_class = RouteModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('code')
    filterset_class = RouteFilter

class LocationFilter(django_filters.FilterSet):
    class Meta:
        model = LocationModel
        fields = {
            'distributor_center': ['exact'],
            'id': ['exact'],
        }
class LocationModelViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin
                                , viewsets.GenericViewSet):
    queryset = LocationModel.objects.all()
    serializer_class = LocationModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('code')
    filterset_class = LocationFilter
