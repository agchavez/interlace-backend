from rest_framework import mixins, viewsets
from rest_framework import filters

from ..serializer import CountrySerializer
from ..models import CountryModel


class CountryViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet,
                     mixins.RetrieveModelMixin):
    queryset = CountryModel.objects.all()
    serializer_class = CountrySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    ordering_fields = ['name']



