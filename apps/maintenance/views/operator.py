from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import OperatorModel

# Serializers
from ..serializer import OperatorModelSerializer

class OperatorFilter(django_filters.FilterSet):
    class Meta:
        model = OperatorModel
        fields = {
            'distributor_center': ['exact']
        }
class OperatorModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin
                            , viewsets.GenericViewSet):
     queryset = OperatorModel.objects.all()
     serializer_class = OperatorModelSerializer
     filter_backends = [filters.SearchFilter, DjangoFilterBackend]
     search_fields = ('first_name', 'last_name')
     filterset_class = OperatorFilter
