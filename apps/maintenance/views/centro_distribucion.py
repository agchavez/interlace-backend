
from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import DistributorCenter, LocationModel, RouteModel

# Serializers
from ..serializer import DistributorCenterSerializer, RouteModelSerializer, LocationModelSerializer
from ...user.views.user import CustomAccessPermission


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
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_distributorcenter'],
        'POST': ['maintenance.add_distributorcenter'],
        'PUT': ['maintenance.change_distributorcenter'],
        'PATCH': ['maintenance.change_distributorcenter'],
        'DELETE': ['maintenance.delete_distributorcenter'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

class RouteFilter(django_filters.FilterSet):
    class Meta:
        model = RouteModel
        fields = {
            'distributor_center': ['exact'],
            'location': ['exact'],
            'id': ['exact'],
        }

class RouteModelViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.CreateModelMixin,
                                viewsets.GenericViewSet):
    queryset = RouteModel.objects.all()
    serializer_class = RouteModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('code')
    filterset_class = RouteFilter
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_routemodel'],
        'POST': ['maintenance.add_routemodel'],
        'PUT': ['maintenance.change_routemodel'],
        'PATCH': ['maintenance.change_routemodel'],
        'DELETE': ['maintenance.delete_routemodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

class LocationFilter(django_filters.FilterSet):
    class Meta:
        model = LocationModel
        fields = {
            'distributor_center': ['exact'],
            'id': ['exact'],
            'name': ['icontains'],
        }
class LocationModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.CreateModelMixin
                                , viewsets.GenericViewSet):
    queryset = LocationModel.objects.all()
    serializer_class = LocationModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'code']
    filterset_class = LocationFilter
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_locationmodel'],
        'POST': ['maintenance.add_locationmodel'],
        'PUT': ['maintenance.change_locationmodel'],
        'PATCH': ['maintenance.change_locationmodel'],
        'DELETE': ['maintenance.delete_locationmodel'],

    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

