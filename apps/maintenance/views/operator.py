from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import OperatorModel

# Serializers
from ..serializer import OperatorModelSerializer
from ...user.views.user import CustomAccessPermission


class OperatorFilter(django_filters.FilterSet):
    class Meta:
        model = OperatorModel
        fields = {
            'distributor_center': ['exact'],
            'id': ['exact'],
        }


class OperatorModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin
                            , viewsets.GenericViewSet):
     queryset = OperatorModel.objects.all()
     serializer_class = OperatorModelSerializer
     filter_backends = [filters.SearchFilter, DjangoFilterBackend]
     search_fields = ('first_name', 'last_name')
     filterset_class = OperatorFilter
     permission_classes = [CustomAccessPermission]

     PERMISSION_MAPPING = {
         'GET': ['maintenance.view_operatormodel'],
            'POST': ['maintenance.add_operatormodel'],
            'PUT': ['maintenance.change_operatormodel'],
            'PATCH': ['maintenance.change_operatormodel'],
            'DELETE': ['maintenance.delete_operatormodel'],

     }

     def get_required_permissions(self, http_method):
         return self.PERMISSION_MAPPING.get(http_method, [])


