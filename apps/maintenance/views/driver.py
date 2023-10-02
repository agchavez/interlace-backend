from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import DriverModel

# Serializers
from ..serializer import DriverModelSerializer
from ...user.views.user import CustomAccessPermission


class DriverFilter(django_filters.FilterSet):
    class Meta:
        model = DriverModel
        fields = {
            'id': ['exact'],
        }


class DriverModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.CreateModelMixin
                            , viewsets.GenericViewSet):
     queryset = DriverModel.objects.all()
     serializer_class = DriverModelSerializer
     filter_backends = [filters.SearchFilter, DjangoFilterBackend]
     search_fields = ('first_name', 'last_name')
     filterset_class = DriverFilter
     permission_classes = [CustomAccessPermission]

     PERMISSION_MAPPING = {
         'GET': ['maintenance.view_drivermodel'],
            'POST': ['maintenance.add_drivermodel'],
            'PUT': ['maintenance.change_drivermodel'],
            'PATCH': ['maintenance.change_drivermodel'],
            'DELETE': ['maintenance.delete_drivermodel'],
     }

     def get_required_permissions(self, http_method):
         return self.PERMISSION_MAPPING.get(http_method, [])


