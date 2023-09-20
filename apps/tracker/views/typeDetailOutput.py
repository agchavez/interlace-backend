# rest_framework
from rest_framework import viewsets, mixins

#django filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from ..exceptions.tracker import ProductOutputRegistered
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
        permission_classes = [CustomAccessPermission]
        filter_backends = [DjangoFilterBackend]
        filterset_class = TrackerDetailOutputFilterSet
        # Mapeo de métodos HTTP a los permisos requeridos
        PERMISSION_MAPPING = {
            'GET': ['tracker.view_trackermodel'],
            'POST': ['tracker.add_trackermodel'],
            'PUT': ['tracker.change_trackermodel'],
            'PATCH': ['tracker.change_trackermodel'],
            'DELETE': ['tracker.delete_trackermodel'],
        }

        def get_required_permissions(self, http_method):
            return self.PERMISSION_MAPPING.get(http_method, [])

        # Funcion de crear
        def create(self, request, *args, **kwargs):
            # validar que no existe un producto en el tracker
            tracker = request.data['tracker']
            product = request.data['product']
            if TrackerDetailOutputModel.objects.filter(tracker=tracker, product=product).exists():
                raise ProductOutputRegistered()
            return super().create(request, *args, **kwargs)

