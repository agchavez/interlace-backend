# rest_framework
from rest_framework import viewsets, mixins

#django filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from ..models import TrackerDetailOutputModel
from ..serializers import TrackerDetailOutputSerializer
from ...user.views.user import CustomAccessPermission


class TrackerDetailOutputFilterSet(django_filters.FilterSet):
    class Meta:
        model = TrackerDetailOutputModel
        # rango de created_at
        fields = {
            'tracker': ['exact'],
            'product': ['exact'],
            'created_at': ['exact', 'gte', 'lte']
        }


class TrackerDetailOutputView(
                                viewsets.GenericViewSet,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.CreateModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin):
        queryset = TrackerDetailOutputModel.objects.all()
        serializer_class = TrackerDetailOutputSerializer
        permission_classes = []
        filter_backends = [DjangoFilterBackend]
        filterset_class = TrackerDetailOutputFilterSet
        # Mapeo de métodos HTTP a los permisos requeridos
        PERMISSION_MAPPING = {
            'GET': [],
            'POST': ['add_trackermodel'],
            'PUT': ['change_trackermodel'],
            'PATCH': ['change_trackermodel'],
            'DELETE': ['delete_trackermodel'],
        }

