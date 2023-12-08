# rest_framework
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from rest_framework import viewsets, mixins, status

# transactions
from django.db import transaction

# actions
from rest_framework.decorators import action

# django filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from ..exceptions.tracker_t2 import DeleteStateCreated
from ..models import OutputT2Model, OutputDetailT2Model, TrackerOutputT2Model
from ..serializers import OutputDetailT2Serializer, TrackerOutputT2Serializer, OutputT2Serializer, \
    OutputTrackerT2MassiveSerializer, OutputT2ListSerializer
from ..utils.tracker_t2 import create_output_t2
from ...order.exceptions.order_detail import PermissionDenied
from ...user.views.user import CustomAccessPermission
from ..utils.processes import apply_output_movements_t2

class OutputT2FilterSet(django_filters.FilterSet):
    # filtrar por multiple status
    status = django_filters.MultipleChoiceFilter(
        choices=OutputT2Model.choices_status,
        field_name='status',
        label='Estado'
    )

    id = django_filters.NumberFilter(
        field_name='id',
        label='ID'
    )

    distributor_center = django_filters.NumberFilter(
        field_name='distributor_center',
        label='Centro de distribución'
    )

    date = django_filters.DateFromToRangeFilter(
        field_name='created_at',
        label='Fecha de creación'
    )

    class Meta:
        model = OutputT2Model
        # rango de created_at
        fields = ('status', 'distributor_center', 'id')



class OutputT2View(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin):
    queryset = OutputT2Model.objects.all()
    serializer_class = OutputT2Serializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OutputT2FilterSet

    permission_classes = [CustomAccessPermission]
    # Mapeo de métodos HTTP a los permisos requeridos
    PERMISSION_MAPPING = {
        'GET': ['tracker.view_outputt2model'],
        'POST': ['tracker.add_outputt2model'],
        'PUT': ['tracker.change_outputt2model'],
        'PATCH': ['tracker.change_outputt2model'],
        'DELETE': ['tracker.delete_outputt2model'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    def list(self, request, *args, **kwargs):
        # serializer solo para listar
        queryset = self.filter_queryset(self.get_queryset())

        serializer_class = OutputT2ListSerializer
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(self.queryset, many=True)
        return Response(serializer.data)

    # Funcion de crear
    def create(self, request, *args, **kwargs):
        # validar si manda el excel, la localidad
        (data, status_code) = create_output_t2(request)
        if status_code == status.HTTP_201_CREATED:
            return Response({
                'id': data.id,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(data, status=status_code)

    # solo se puede eliminar si no tiene detalle de salida y el status es CREATED
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == 'APPLIED':
            raise DeleteStateCreated()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Obtner mis salidas segun el usuario y eel cd asociado para el grupo 'SUPERVISOR' mostrar los que esten con status 'CREATED', 'REJECTED'
    # Para el rol de 'AYUDANTE DE BODEGA' mostrar las salidas con status 'AUTHORIZED', 'CHECKED'
    @action(detail=False, methods=['get'], url_path='my-outputs')
    def my_outputs(self, request, *args, **kwargs):
        try:
            cd = request.user.centro_distribucion
        except ObjectDoesNotExist:
            raise PermissionDenied()

        if request.user.groups.filter(name='AYUDANTE DE BODEGA INTERNA').exists():
            outputs = OutputT2Model.objects.filter(distributor_center=cd, status__in=['CREATED', 'REJECTED'])
        elif request.user.groups.filter(name='SUPERVISOR').exists():
            outputs = OutputT2Model.objects.filter(distributor_center=cd, status__in=['AUTHORIZED', 'CHECKED'])
        else:
            raise PermissionDenied()

        return Response(OutputT2Serializer(outputs, many=True).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='apply')
    def apply(self, request, *args, **kwargs):
        output = self.get_object_or_404()

        self.check_permissions_created(request, output)

        self.check_details_status(output)

        user = request.user

        # verificar que el usuario sea un supervisor  y tenga el mismo cd que la salida
        if user.groups.filter(name='SUPERVISOR').exists():
            if user.centro_distribucion != output.distributor_center:
                raise PermissionDenied()
        else:
            raise PermissionDenied()
        with transaction.atomic():
            self.apply_output(output, user)

        return Response(OutputT2Serializer(output).data, status=status.HTTP_200_OK)

    def get_object_or_404(self):
        return get_object_or_404(OutputT2Model, pk=self.kwargs['pk'])

    def check_permissions_created(self, request, output):
        try:
            cd = request.user.centro_distribucion
        except ObjectDoesNotExist:
            raise PermissionDenied()

        if cd != output.distributor_center:
            raise PermissionDenied()

    def check_details_status(self, output):
        unauthorized_details = OutputDetailT2Model.objects.filter(
            output=output,
            status__in=['CREATED', 'CHECKED', 'REJECTED']
        ).exists()

        if unauthorized_details:
            # TODO: Estandarisar los mensajes de error
            return Response({
                'error': 'No se puede aplicar la salida, hay detalles pendientes por autorizar'
            }, status=status.HTTP_400_BAD_REQUEST)

    def apply_output(self, output, user):
        # TODO: Insertar las salidas de inventario por T2
        apply_output_movements_t2(output.id, user.id)
        OutputT2Model.objects.filter(pk=output.pk).update(status='APPLIED', user_applied=user)
        OutputDetailT2Model.objects.filter(
            output=output
        ).update(status='APPLIED')


class OutputDetailT2FilterSet(django_filters.FilterSet):
    class Meta:
        model = OutputDetailT2Model
        # rango de created_at
        fields = {
            'output': ['exact'],
            'product': ['exact'],
            'created_at': ['exact', 'gte', 'lte']
        }


class OutputDetailT2View(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = OutputDetailT2Model.objects.all()
    serializer_class = OutputDetailT2Serializer
    permission_classes = [CustomAccessPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OutputDetailT2FilterSet
    # Mapeo de métodos HTTP a los permisos requeridos
    PERMISSION_MAPPING = {
        'GET': ['tracker.view_outputdetailt2model'],
        'POST': ['tracker.add_outputdetailt2model'],
        'PUT': ['tracker.change_outputdetailt2model'],
        'PATCH': ['tracker.change_outputdetailt2model'],
        'DELETE': ['tracker.delete_outputdetailt2model'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    # solo se puede eliminar si el status es CREATED y no tiene tracker
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.output.status != 'CREATED':
            raise DeleteStateCreated()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='massive-create')
    def massive_create(self, request, *args, **kwargs):
        output_detail = self.get_object()
        serializer = OutputTrackerT2MassiveSerializer(data=request.data, context={'output_detail': output_detail})
        if serializer.is_valid():
            # validar que el usuario tenga permisos para crear
            try:
                cd = request.user.centro_distribucion
            except:
                raise PermissionDenied()

            if cd != output_detail.output.distributor_center:
                raise PermissionDenied()

            # validar que el status de la salida sea CREATED

            list = serializer.validated_data['list']
            list_delete = serializer.validated_data['list_delete']
            # TODO: MANEJO DE ESTADOS validacion

            # transaccion
            with transaction.atomic():
                if list_delete:
                    # eliminar los tracker_output_t2 que esten en la lista de list_delete
                    TrackerOutputT2Model.objects.filter(id__in=list_delete).delete()

                for data in list:
                    # crear el tracker output t2
                    TrackerOutputT2Model.objects.create(
                        output_detail=output_detail,
                        tracker_detail_id=data['tracker_detail_product'],
                        quantity=data['quantity']
                    )
                # si la suma de todos los tracker_output_t2 con el mismo output_detail es igual a la cantidad de la salida, cambiar el status a CHECKED
                sum_quantity = \
                    TrackerOutputT2Model.objects.filter(output_detail=output_detail).aggregate(total=Sum('quantity'))[
                        'total']
                if sum_quantity == output_detail.quantity:
                    output_detail.status = 'CHECKED'
                    output_detail.save()
                else:
                    output_detail.status = 'CREATED'
                    output_detail.save()

            return Response(OutputDetailT2Serializer(output_detail).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrackerOutputT2FilterSet(django_filters.FilterSet):
    class Meta:
        model = TrackerOutputT2Model
        # rango de created_at
        fields = {
            'created_at': ['exact', 'gte', 'lte']
        }


class TrackerOutputT2View(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = TrackerOutputT2Model.objects.all()
    serializer_class = TrackerOutputT2Serializer
    permission_classes = [CustomAccessPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TrackerOutputT2FilterSet
    # Mapeo de métodos HTTP a los permisos requeridos
    PERMISSION_MAPPING = {
        'GET': ['tracker.view_trackeroutputt2model'],
        'POST': ['tracker.add_trackeroutputt2model'],
        'PUT': ['tracker.change_trackeroutputt2model'],
        'PATCH': ['tracker.change_trackeroutputt2model'],
        'DELETE': ['tracker.delete_trackeroutputt2model'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])
