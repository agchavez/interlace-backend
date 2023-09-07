from rest_framework import mixins, viewsets
from rest_framework import filters
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import ProductModel

# Serializers
from ..serializer import ProductModelSerializer


class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = ProductModel
        fields = {
            'name': ['exact'],
            'bar_code': ['exact'],
            'id': ['exact'],
        }


class ProductModelViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin
    , viewsets.GenericViewSet):
    queryset = ProductModel.objects.all()
    serializer_class = ProductModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('name', 'sap_code', 'brand')
    filterset_class = ProductFilter
