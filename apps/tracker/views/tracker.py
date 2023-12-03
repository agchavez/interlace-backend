from datetime import datetime

from django.contrib.auth.models import AnonymousUser
from django.db.models import Sum, Q, F
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
from apps.maintenance.models import TrailerModel, TransporterModel, DistributorCenter, ProductModel
from apps.user.models import UserModel as User
from apps.tracker.exceptions.tracker import TrackerCompleted, UserWithoutDistributorCenter, TrackerCompletedDetail, \
    TrackerCompletedDetailProduct, InputDocumentNumberRegistered, InputDocumentNumberIsNotNumber, QuantityRequired, \
    TrackerCompletedDetailRequired, InputDocumentNumberRequired, OutputDocumentNumberRequired, TransferNumberRequired, \
    OperatorRequired, OutputTypeRequired, InvoiceRequired, ContainerNumberRequired, PlateNumberRequired, DriverRequired, \
    OriginLocationRequired, AccountedRequired,  FileTooLarge, FileNotExists

from apps.user.views.user import CustomAccessPermission
from apps.tracker.models import TrackerDetailOutputModel
from rest_framework.filters import OrderingFilter
from django.http import HttpResponse
from ..utils.processes import apply_output_movements
from ...order.utils.update import validate_and_update_order_detail, update_order_detail


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
    user = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name='user__id',
        to_field_name='id'
    )

    date = django_filters.DateFromToRangeFilter(
        field_name='created_at',
        label='Fecha de creación'
    )

    distributor_center = django_filters.ModelMultipleChoiceFilter(
        queryset=DistributorCenter.objects.all(),
        field_name='distributor_center__id',
        to_field_name='id'
    )

    id = django_filters.NumberFilter(
        field_name='id',
        label='ID'
    )

    status = django_filters.CharFilter(
        field_name='status',
        label='Status',
        method='filter_status',
    )

    def filter_status(self, queryset, name, value):
        values = value.split(',')
        return queryset.filter(status__in=values)


    class Meta:
        model = TrackerModel
        fields = ('transporter', 'trailer', 'status','type', 'user', 'date', 'distributor_center', 'id')


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
        'GET': ['tracker.view_trackermodel'],
        'POST': ['tracker.add_trackermodel'],
        'PUT': ['tracker.change_trackermodel'],
        'PATCH': ['tracker.change_trackermodel'],
        'DELETE': ['tracker.delete_trackermodel'],
    }

    # Si el usuario es del grupo solo SUPERVISOR solo puede ver los trackers de su centro de distribucion
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.groups.filter(name='SUPERVISOR').exists():
    #         return TrackerModel.objects.filter(distributor_center=user.centro_distribucion)
    #     return TrackerModel.objects.all()

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    # Sobrescribe el método perform_create para asignar el usuario y el centro de distribución.
    def create(self, request, *args, **kwargs):
        user, center = validate_create_tracker(request)
        request.data['user'] = user.id
        request.data['distributor_center'] = center.id
        # Buscar operadores de tracker anteriores para el mismo centro de distribucion
        tracker = TrackerModel.objects.filter(distributor_center=center, operator_1__isnull=False, operator_2__isnull=False).last()
        if tracker:
            request.data['operator_1'] = tracker.operator_1.id
            request.data['operator_2'] = tracker.operator_2.id
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
        queryset = TrackerModel.objects.filter(status='EDITED', distributor_center=user.centro_distribucion)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Completar un tracker
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, *args, **kwargs):
        tracker = self.get_object()
        validate_complete_tracker(tracker)
        if tracker.order:
            update_order_detail(tracker.order, tracker)

        tracker.complete()
        # la fecha de completado se actualiza en el modelo
        tracker.completed_date = datetime.now()
        tracker.save()

        # aplicar movimientos de salida
        apply_output_movements.delay(tracker.id, request.user.id)
        return Response({'detail': 'Se completo el tracker'}, status=status.HTTP_200_OK)

    # Informacion del dashboard por centro de distribucion de usuarios
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request, *args, **kwargs):
        # Solo para los usuario con centro de distribucion
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        if user.centro_distribucion:
            queryset = self.filter_queryset(self.get_queryset()).filter(distributor_center=user.centro_distribucion)
        # Ultimos 5 tracker completado
        last_trackers = queryset.filter(status='COMPLETE').order_by('-completed_date')[:5]
        # Total de trackers completados
        total_trackers_completed = queryset.filter(status='COMPLETE').count()
        # Total de trackers pendientes
        total_trackers_pending = queryset.filter(status='PENDING').values('created_at', 'status', 'id').order_by('created_at')[:10]
        # Tiempo promedio en completar un tracker
        time_average = queryset.filter(status='COMPLETE').aggregate(Sum('time_invested'))
        # Tiempo promedio en completar un tracker
        time_average = time_average.get('time_invested__sum') / total_trackers_completed if total_trackers_completed > 0 else 0
        return Response({
            'total_trackers_completed': total_trackers_completed,
            'total_trackers_pending': total_trackers_pending,
            'time_average': time_average,
            'last_trackers': TrackerSerializer(last_trackers, many=True).data
        }, status=status.HTTP_200_OK)
    # Cargar archivo
    @action(detail=True, methods=['patch'], url_path='upload-file')
    def uploadFile(self, request, *args, **kwargs):
        tracker = self.get_object()
        if tracker.status != "EDITED":
            raise TrackerCompleted
        archivo = request.data.get("archivo")
        name = request.data.get("name")
        if archivo is not None:
            if archivo.size > 20*1024*1024:
                raise FileTooLarge
            content = archivo.read()
            tracker.archivo = content
        if name:
            tracker.archivo_name = name
        tracker.save()
        serializer = TrackerSerializer(tracker)
        return Response(serializer.data, status=status.HTTP_200_OK)
    # Descargar archivo
    @action(detail=True, methods=['get'], url_path='get-file')
    def getFile(self, request, *args, **kwargs):
        tracker = self.get_object()
        archivo = tracker.archivo
        if not archivo:
            raise FileNotExists
        response = HttpResponse(archivo, content_type='application/octet-stream',)
        response['Content-Disposition'] = f'attachment; filename="{tracker.archivo_name}"'
        return response

    # ultimos detalles de salida del centro de distribucion
    @action(detail=False, methods=['get'], url_path='last-output')
    def getLastOutput(self, request, *args, **kwargs):
        user = request.user
        cd = user.centro_distribucion
        limit = request.GET.get("limit") 
        limit = int(limit) if limit is not None else 15
        if cd is None:
            raise UserWithoutDistributorCenter()
        trackers = TrackerModel.objects.filter(distributor_center=cd).exclude(output_type = 9).order_by('-created_at')
        outputData = []
        for tracker in trackers:
            if tracker.output_type is not None:
                opt = {}
                opt["required_details"]=tracker.output_type.required_details
                opt["tracking"]=tracker.pk
                opt["output_type_name"]=tracker.output_type.name
                if tracker.output_type.required_details:
                    details = TrackerDetailOutputModel.objects.filter(tracker=tracker).exclude(product__sap_code="3501451")
                    for detail in details:
                        opt["sap_code"]=detail.product.sap_code
                        opt["product_name"]=detail.product.name
                        opt["quantity"]=detail.quantity
                        opt["expiration_date"]=detail.expiration_date
                        outputData.append(opt)
                        if len(outputData) > limit:
                            break
                else:
                    outputData.append(opt)
                if len(outputData) > limit:
                    break
        # tracker compeltados el dia de hoy
        tracker_completed_today = TrackerModel.objects.filter(distributor_center=cd, status='COMPLETE', created_at__date=datetime.now().date()).count()


        # cantidad de pallets recibidos hoy y agrupados por producto
        products = TrackerDetailProductModel.objects.filter(tracker_detail__tracker__distributor_center=cd, created_at__date=datetime.now().date()).values('tracker_detail__product__id', 'tracker_detail__product__name').annotate(total=Sum('quantity'))

        # Helectrolitos totales del dia de hoy = cantidad pallets x producto.boxes_pre_pallet x producto.helectrolitos
        total_hele = 0
        total_pallets = 0
        for product in products:
            product_obj = ProductModel.objects.get(id=product['tracker_detail__product__id'])
            total_hele += product['total'] * product_obj.boxes_pre_pallet * product_obj.helectrolitos
            total_pallets += product['total']
        return Response({
            'results': outputData[:limit],
            'tracker_completed_today': tracker_completed_today,
            'total_hele': total_hele,
            'total_pallets': total_pallets
        }, status=status.HTTP_200_OK)


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
        'GET': ['tracker.view_trackermodel'],
        'POST': ['tracker.add_trackermodel'],
        'PUT': ['tracker.change_trackermodel'],
        'PATCH': ['tracker.change_trackermodel'],
        'DELETE': ['tracker.delete_trackermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

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


class TrackerDetailProductModelFilter(django_filters.FilterSet):
        order_by = django_filters.OrderingFilter(
            fields=(
                ('created_at', 'created_at')
            )
        )


        class Meta:
            model = TrackerDetailProductModel
            fields = {
                'tracker_detail': ['exact'],
                'tracker_detail__tracker': ['exact'],
                'tracker_detail__tracker__distributor_center': ['exact'],
                'tracker_detail__product': ['exact'],
                'created_at': ['gte', 'lte'],
                'expiration_date': ['gte', 'lte', 'exact'],
                'id': ['exact'],
                'tracker_detail__tracker__status': ['exact'],
                'tracker_detail__tracker__user': ['exact'],

            }

class TrackerDetailProductModelViewSet(mixins.ListModelMixin,
                                       mixins.RetrieveModelMixin,
                                       mixins.CreateModelMixin,
                                       mixins.UpdateModelMixin,
                                       mixins.DestroyModelMixin
    , viewsets.GenericViewSet):
    # Evitar los que el tracker_detail este en null
    queryset = TrackerDetailProductModel.objects.filter(tracker_detail__isnull=False)
    serializer_class = TrackerDetailProductModelSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = TrackerDetailProductModelFilter
    search_fields = ()
    permission_classes = [CustomAccessPermission]
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

    def partial_update(self, request, *args, **kwargs):
        # la cantidad disponible es igual a la cantidad
        instance = self.get_object()
        request.data['available_quantity'] = request.data['quantity'] * instance.tracker_detail.product.boxes_pre_pallet
        return super().partial_update(request, *args, **kwargs)


    def list(self, request, *args, **kwargs):
        # agregar filtro adicional
        queryset = self.filter_queryset(self.get_queryset())

        user = request.user

        if user is not isinstance(user, AnonymousUser) and hasattr(user, 'centro_distribucion'):
            if user.centro_distribucion:
                queryset = queryset.filter(tracker_detail__tracker__distributor_center=user.centro_distribucion)

        # filtrar por turno segun query param 'A': 06:00:00 - 14:00:00, 'B': 14:00:00 - 22:30:00, 'C': 22:30:00 - 06:00:00
        shift = request.GET.get('shift')
        if shift is not None and shift in ['A', 'B', 'C']:
            if shift == 'A':
                queryset = queryset.filter(created_at__hour__gte=6, created_at__hour__lte=14)
            if shift == 'B':
                queryset = queryset.filter(created_at__hour__gte=14, created_at__hour__lte=22)
            if shift == 'C':
                queryset = queryset.filter(Q(created_at__hour__gte=22.5) | Q(created_at__hour__lt=6))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
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
        #if TrackerModel.objects.filter(transfer_number=data.get('transfer_number')).exclude(
                #id=instance.id).exists():
            #raise InputDocumentNumberRegistered()
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

    # la localidad de origen es requerida
    if not tracker.origin_location:
        raise OriginLocationRequired()
    # Validar que si hay una orden
    if tracker.order:
        validate_and_update_order_detail(tracker.order, tracker)

    if tracker.type == 'LOCAL':
        # Validar numero de entrada, salida y traslado
        if not tracker.input_document_number:
            raise InputDocumentNumberRequired()
        if not tracker.output_document_number:
            raise OutputDocumentNumberRequired()
        if not tracker.transfer_number:
            raise TransferNumberRequired()
        if not tracker.driver:
            raise DriverRequired()

        # Validar la data del oeperador y las fechas de entrada y salida
        if not tracker.operator_1 or not tracker.input_date or not tracker.output_date:
            raise OperatorRequired()

        # Validaciones para el tipo de salida del producto
        if not tracker.output_type:
            raise OutputTypeRequired()
        # El contabilizado es obligatorio solo si el tipo de salida no es VACIO
        if not tracker.accounted and tracker.output_type.id != 9:
            raise AccountedRequired()

    if tracker.type == 'IMPORT':
        # Validar numero de factura y numero de contenedor
        if not tracker.invoice_number:
            raise InvoiceRequired()
        if not tracker.container_number:
            raise ContainerNumberRequired()
        if not tracker.driver_import:
            raise DriverRequired()
        if not tracker.transfer_number:
            raise TransferNumberRequired()
    # validar numero de placa y driver
    if not tracker.plate_number:
        raise PlateNumberRequired()

    # Validar que todos los detalles de tracker tengan la cantidad completa
    for tracker_detail in tracker.tracker_detail.all():
        sum_quantity = TrackerDetailProductModel.objects.filter(tracker_detail=tracker_detail).aggregate(
            Sum('quantity'))
        if sum_quantity.get('quantity__sum') != tracker_detail.quantity:
            raise QuantityRequired()
    return True
