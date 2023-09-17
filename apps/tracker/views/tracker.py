from datetime import datetime

from django.db.models import Sum
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
from apps.tracker.exceptions.tracker import TrackerCompleted, UserWithoutDistributorCenter, TrackerCompletedDetail, \
    TrackerCompletedDetailProduct, InputDocumentNumberRegistered, InputDocumentNumberIsNotNumber, QuantityRequired, \
    TrackerCompletedDetailRequired, InputDocumentNumberRequired, OutputDocumentNumberRequired, TransferNumberRequired, \
    OperatorRequired, OutputTypeRequired
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
        'GET': ['view_trackermodel'],
        'POST': ['add_trackermodel'],
        'PUT': ['change_trackermodel'],
        'PATCH': ['change_trackermodel'],
        'DELETE': ['delete_trackermodel'],
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
        if self.get_object().status == 'COMPLETE':
            raise TrackerCompleted()
        return super().destroy(request, *args, **kwargs)

    # Sobrescribir metodo patch para dar respuesta solo de un OK
    def partial_update(self, request, *args, **kwargs):
        validate_create_tracker(request, self.get_object().id)
        return super().partial_update(request, *args, **kwargs)

    # listar los trackers de un usuario que esten PENDING
    @action(detail=False, methods=['get'], url_path='my-trackers')
    def my_trackers(self, request, *args, **kwargs):
        user = request.user
        queryset = TrackerModel.objects.filter(user=user, status='PENDING')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Completar un tracker
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, *args, **kwargs):
        tracker = self.get_object()
        validate_complete_tracker(tracker)
        tracker.complete()
        # la fecha de completado se actualiza en el modelo
        tracker.completed_date = datetime.now()
        tracker.save()
        return Response({'detail': 'Se completo el tracker'}, status=status.HTTP_200_OK)


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
    permission_classes = [CustomAccessPermission]
    # Mapeo de métodos HTTP a los permisos requeridos
    PERMISSION_MAPPING = {
        'GET': ['view_trackermodel'],
        'POST': ['add_trackermodel'],
        'PUT': ['change_trackermodel'],
        'PATCH': ['change_trackermodel'],
        'DELETE': ['delete_trackermodel'],
    }

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

    def destroy(self, request, *args, **kwargs):
        if self.get_object().tracker.status == 'COMPLETE':
            raise TrackerCompletedDetail()
        return super().destroy(request, *args, **kwargs)


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
    permission_classes = [CustomAccessPermission]
    # Mapeo de métodos HTTP a los permisos requeridos
    PERMISSION_MAPPING = {
        'GET': ['view_trackermodel'],
        'POST': ['add_trackermodel'],
        'PUT': ['change_trackermodel'],
        'PATCH': ['change_trackermodel'],
        'DELETE': ['delete_trackermodel'],
    }

    def destroy(self, request, *args, **kwargs):
        if self.get_object().tracker_detail.tracker.status == 'COMPLETE':
            raise TrackerCompletedDetailProduct()
        return super().destroy(request, *args, **kwargs)


def validate_create_tracker(request, id=None):
    usuario = request.user
    distribuidor = usuario.centro_distribucion
    data = request.data
    instance = None
    if id is not None:
        instance = TrackerModel.objects.filter(id=id).first()

    # Validar si el documento de entrada ya esta registrado
    if data.get('input_document_number') and instance:
        if TrackerModel.objects.filter(input_document_number=data.get('input_document_number')).exclude(
                id=instance.id).exists():
            raise InputDocumentNumberRegistered()
        # El documento de entrada no debe ser numerico en el caso que lo mande
        if not data.get('input_document_number').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Validaciones de documento de salida
    if data.get('output_document_number') and instance:
        if TrackerModel.objects.filter(output_document_number=data.get('output_document_number')).exclude(
                id=instance.id).exists():
            raise InputDocumentNumberRegistered()
        # El documento de salida no debe ser numerico en el caso que lo mande
        if not data.get('output_document_number').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Validaciones de numero de traslado
    if data.get('transfer_number') and instance:
        if TrackerModel.objects.filter(transfer_number=data.get('transfer_number')).exclude(
                id=instance.id).exists():
            raise InputDocumentNumberRegistered()
        # El numero de traslado no debe ser numerico en el caso que lo mande
        if not data.get('transfer_number').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Validacion de contabilzado
    if data.get('accounted') and instance:
        if not data.get('accounted').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Vlidar centro de distribucion del usuario
    if distribuidor is None:
        raise UserWithoutDistributorCenter()
    return (usuario, distribuidor)


# Validaciones para marcar completado un tracker
def validate_complete_tracker(tracker):
    # Si ya esta completado, no se puede completar de nuevo
    if tracker.status == 'COMPLETE':
        raise TrackerCompleted()
    # Debe exister almenos un detalle de tracker
    if tracker.tracker_detail.count() == 0:
        raise TrackerCompletedDetailRequired()
    # Validar numero de entrada, salida y traslado
    if not tracker.input_document_number:
        raise InputDocumentNumberRequired()
    if not tracker.output_document_number:
        raise OutputDocumentNumberRequired()
    if not tracker.transfer_number:
        raise TransferNumberRequired()

    # Validar la data del oeperador y las fechas de entrada y salida
    if not tracker.operator_1 or not tracker.input_date or not tracker.output_date:
        raise OperatorRequired()

    # Validaciones para el tipo de salida del producto
    if not tracker.output_type:
        raise OutputTypeRequired()
    # Validar que todos los detalles de tracker tengan la cantidad completa
    for tracker_detail in tracker.tracker_detail.all():
        sum_quantity = TrackerDetailProductModel.objects.filter(tracker_detail=tracker_detail).aggregate(
            Sum('quantity'))
        if sum_quantity.get('quantity__sum') != tracker_detail.quantity:
            raise QuantityRequired()
    return True
