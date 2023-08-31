
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import  Response

# django filters
from django_filters.rest_framework import DjangoFilterBackend

# Models
from ..models import CentroDistribucion

# Serializers
from ..serializer import CentroDistribucionSerializer

class CentroDistribucionViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin
                                , viewsets.GenericViewSet):
    queryset = CentroDistribucion.objects.all()
    serializer_class = CentroDistribucionSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('nombre', 'direccion')
    # Quitar la paginacion
    pagination_class = None
