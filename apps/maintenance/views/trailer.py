from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import TrailerModel, TransporterModel

# Serializers
from ..serializer import TrailerModelSerializer, TransporterModelSerializer
from apps.user.views.user import CustomAccessPermission

class TrailerFilter(django_filters.FilterSet):
    class Meta:
        model = TrailerModel
        fields = {
            'id': ['exact'],
        }


class TrailerModelViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          viewsets.GenericViewSet):
    queryset = TrailerModel.objects.all()
    serializer_class = TrailerModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('code',)
    filterset_class = TrailerFilter
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_trailermodel'],
        'POST': ['maintenance.add_trailermodel'],
        'PUT': ['maintenance.change_trailermodel'],
        'PATCH': ['maintenance.change_trailermodel'],
        'DELETE': ['maintenance.delete_trailermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])


class TransporterModelViewSet(mixins.ListModelMixin
    , viewsets.GenericViewSet):
    queryset = TransporterModel.objects.all()
    serializer_class = TransporterModelSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('tractor', 'code', 'name', 'head')
    permission_classes = [CustomAccessPermission]

    PERMISSION_MAPPING = {
        'GET': ['maintenance.view_transportermodel'],
        'POST': ['maintenance.add_transportermodel'],
        'PUT': ['maintenance.change_transportermodel'],
        'PATCH': ['maintenance.change_transportermodel'],
        'DELETE': ['maintenance.delete_transportermodel'],

    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])
