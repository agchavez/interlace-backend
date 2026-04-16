
from rest_framework import mixins, viewsets
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from ..exceptions.maintenance import LotAlreadyExistsError, NoDistributionCenterError
# Models
from ..models import DistributorCenter, LocationModel, RouteModel, LotModel, DCShiftModel

# Serializers
from ..serializer import DistributorCenterSerializer, RouteModelSerializer, LocationModelSerializer, LotModelSerializer
from ..serializer.centro_distribucion import DCShiftSerializer
from ...user.views.user import CustomAccessPermission


class CentroDistribucionFilter(django_filters.FilterSet):
    class Meta:
        model = DistributorCenter
        fields = {
            'country_code': ['exact'],
            'id': ['exact'],
        }

ACTIVE_DISTRIBUTION_CENTERS = [1, 2]  # CD LA GRANJA (1), CD COMAYAGUA (2)

class CentroDistribucionViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin
                                ,mixins.CreateModelMixin,
                                mixins.UpdateModelMixin
                                , viewsets.GenericViewSet):
    queryset = DistributorCenter.objects.filter(id__in=ACTIVE_DISTRIBUTION_CENTERS)
    serializer_class = DistributorCenterSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['name', 'location_distributor_center__code']
    filterset_class = CentroDistribucionFilter
    permission_classes = []

    def get_queryset(self):
        return DistributorCenter.objects.filter(id__in=ACTIVE_DISTRIBUTION_CENTERS)

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
    permission_classes = [IsAuthenticated]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_locationmodel'],
        'POST': ['maintenance.add_locationmodel'],
        'PUT': ['maintenance.change_locationmodel'],
        'PATCH': ['maintenance.change_locationmodel'],
        'DELETE': ['maintenance.delete_locationmodel'],

    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

class LotFilter(django_filters.FilterSet):
    class Meta:
        model = LotModel
        fields = {
            'id': ['exact'],
            'code': ['icontains'],
            'distributor_center': ['exact'],
        }

class LotModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.CreateModelMixin
                                , viewsets.GenericViewSet):
    queryset = LotModel.objects.all()
    serializer_class = LotModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['code', 'id']
    filterset_class = LotFilter
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_lotmodel'],
        'POST': ['maintenance.add_lotmodel'],
        'PUT': ['maintenance.change_lotmodel'],
        'PATCH': ['maintenance.change_lotmodel'],
        'DELETE': ['maintenance.delete_lotmodel'],

    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            distributor_center = self.request.user.centro_distribucion
            queryset = queryset.filter(distributor_center=distributor_center)
        except:
            pass
        return queryset
    def create(self, request, *args, **kwargs):
        data = request.data
        if data.get('distributor_center') is None:
            try:
                data['distributor_center'] = request.user.centro_distribucion.id
            except:
                raise NoDistributionCenterError()
        if data.get('code') is not None:
            code= data['code']
            if LotModel.objects.filter(code=code, distributor_center=data['distributor_center']).exists():
                raise LotAlreadyExistsError()
        return super().create(request, *args, **kwargs)


class DCShiftFilter(django_filters.FilterSet):
    class Meta:
        model = DCShiftModel
        fields = {
            'distributor_center': ['exact'],
            'day_of_week': ['exact'],
            'is_active': ['exact'],
        }


class DCShiftViewSet(viewsets.ModelViewSet):
    """Gestión de turnos por Centro de Distribución"""
    queryset = DCShiftModel.objects.all()
    serializer_class = DCShiftSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DCShiftFilter
    permission_classes = [IsAuthenticated]