from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.response import Response
from rest_framework import status
# django filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# Models
from ..models import TrackerModel, TrackerDetailModel, TrackerDetailProductModel
# Serializers
from ..serializers import TrackerSerializer, TrackerDetailModelSerializer, TrackerDetailProductModelSerializer
from apps.maintenance.models import TrailerModel, TransporterModel
from apps.tracker.exceptions.tracker import TrackerCompleted, UserWithoutDistributorCenter
from apps.user.views.user import CustomAccessPermission
class TrackerFilter(django_filters.FilterSet):

    transporter = django_filters.ModelMultipleChoiceFilter(
        queryset=TransporterModel.objects.all(),
        field_name='transporter__id',
        to_field_name='id'
    )
    trailer = django_filters.ModelMultipleChoiceFilter(
        queryset=TrailerModel.objects.all(),
        field_name='trailer__id',
        to_field_name='id'
    )


    class Meta:
        model = TrackerModel
        fields = ('transporter', 'trailer', 'status')



class TrackerModelViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin
        , viewsets.GenericViewSet):
        queryset = TrackerModel.objects.all()
        serializer_class = TrackerSerializer
        filter_backends = [filters.SearchFilter, DjangoFilterBackend]
        search_fields = ('plate_number', 'input_document_number', 'output_document_number')
        filterset_class = TrackerFilter
        permission_classes = [CustomAccessPermission]
        # Mapeo de métodos HTTP a los permisos requeridos
        PERMISSION_MAPPING = {
            'GET': ['view_usermodel'],
            'POST': ['add_usermodel'],
            'PUT': ['change_usermodel'],
            'PATCH': ['change_usermodel'],
            'DELETE': ['delete_usermodel']
        }

        def get_required_permissions(self, http_method):
            return self.PERMISSION_MAPPING.get(http_method, [])

        # Sobrescribe el método perform_create para asignar el usuario y el centro de distribución.
        def create(self, request, *args, **kwargs):
            user, center = validate_create_tracker(request)
            request.data['user'] = user.id
            request.data['distributor_center'] = center.id
            return super().create(request, *args, **kwargs)


        # Sobrescribe el método destroy para verificar que el tracker no este completado
        def destroy(self, request, *args, **kwargs):
            if (self.get_object().status == 'COMPLETE'):
                raise TrackerCompleted()
            return super().destroy(request, *args, **kwargs)


        # Sobrescribir metodo patch para dar respuesta solo de un OK
        def partial_update(self, request, *args, **kwargs):
            return super().partial_update(request, *args, **kwargs)

        # listar los trackers de un usuario que esten PENDING
        @action(detail=False, methods=['get'], url_path='my-trackers')
        def my_trackers(self, request, *args, **kwargs):
            user = request.user
            queryset = TrackerModel.objects.filter(user=user, status='PENDING')
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class TrackerDetailModelViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.CreateModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin
        , viewsets.GenericViewSet):
        queryset = TrackerDetailModel.objects.all()
        serializer_class = TrackerDetailModelSerializer
        filter_backends = [filters.SearchFilter]
        search_fields = ()
        permission_classes = []


        # Creación de un detalle de tracker
        def create(self, request, *args, **kwargs):
            # Si ya existe un detalle de tracker con el mismo tracker y el mismo producto, se actualiza la cantidad
            tracker = request.data.get('tracker')
            product = request.data.get('product')
            quantity = request.data.get('quantity')
            tracker_detail = TrackerDetailModel.objects.filter(tracker=tracker, product=product).first()
            if tracker_detail:
                tracker_detail.quantity = quantity
                tracker_detail.save()
                return Response({'detail': 'Se actualizo la cantidad'}, status=status.HTTP_200_OK)
            return super().create(request, *args, **kwargs)


class TrackerDetailProductModelViewSet(mixins.ListModelMixin,
                                        mixins.RetrieveModelMixin,
                                        mixins.CreateModelMixin,
                                        mixins.UpdateModelMixin,
                                        mixins.DestroyModelMixin
        , viewsets.GenericViewSet):
        queryset = TrackerDetailProductModel.objects.all()
        serializer_class = TrackerDetailProductModelSerializer
        filter_backends = [filters.SearchFilter]
        search_fields = ()
        permission_classes = []


def validate_create_tracker(request):
    usuario = request.user
    distribuidor = usuario.centro_distribucion
    # Vlidar centro de distribucion del usuario
    if distribuidor is None:
        raise UserWithoutDistributorCenter()
    return (usuario, distribuidor)

