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
    pre_sale_date = django_filters.DateFilter(
        field_name='pre_sale_date',
        label='Fecha de preventa'
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

    # Api que recibe un excel de SAP y hace una simulacion con los datos comprando excel con tracker
    @action(detail=True, methods=['post'], url_path='simulate')
    def simulate(self, request, *args, **kwargs):
        output = self.get_object_or_404()
        self.check_permissions_created(request, output)
        # verificar el excel
        excel = request.FILES['excel']
        df = pd.read_excel(excel)
        # validar que el excel tenga las columnas correctas
        if not ({'Ruta_SAP', 'TOUR_ID','Entrega', 'Población', 'Conductor', 'Calle','Cod_Mat', 'Producto', 'Nombre','UM','Cant_UMV'}
                .issubset(df.columns)):
            return Response({
                'error': 'El excel no tiene las columnas correctas'
            }, status=status.HTTP_400_BAD_REQUEST)

        # validar que el excel tenga datos
        if df.empty:
            return Response({
                'error': 'El excel no tiene datos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # limpitar data eliminar filas vacias, cantidad = 0, cod_mat = 0 y todas las rutas que no sean la ruta seleccionada, Cod_Mat que empiecen con 350
        df = df.dropna()
        df = df[df['Cant_UMV'] != 0]
        df = df[df['Cod_Mat'] != 0]
        # Ordenear primeras rutas del conductor osea primero las primera ruta de los conductores y luego las segunda ruta de los conductores yu asi sucesivamente
        df = df.sort_values(by=['Conductor', 'TOUR_ID'], ascending=True)
        # codigo de sap del producto que coincide con 17365
        # df = df[df['Cod_Mat'].astype(str).str.startswith(producto)]

        df = df[~df['Cod_Mat'].astype(str).str.startswith('350')]

        # validar que el excel tenga datos
        if df.empty:
            return Response({
                'error': 'El excel no tiene datos'
            }, status=status.HTTP_400_BAD_REQUEST)

        # sacar lista de TOU_ID, conductor pero que no se repitan para futuros filtros
        tour_id_list = df['TOUR_ID'].unique()
        conductor_list = df['Conductor'].unique()
        client_list = df['Nombre'].unique()
        client_ids = []
        for index, client in enumerate(client_list):
            client_ids.append({
                # quitar espacios en blanco
                'nombre': client.strip(),
                'id': index + 1
            })
        product_list = []
        # tracker detail product de la salida

        # tracker detail all de la salida
        tracker_detail_all = TrackerOutputT2Model.objects.filter(output_detail__output=output)
        data = []
        data_simulated = []
        # manejar la data de los productos, tracker y cantidades para poteriormente ir asignando a cada fila del excel y restando sin afectar la base de datos
        for tracker in tracker_detail_all:
            data.append({
                'tracker_id': tracker.tracker_detail.tracker_detail.tracker.id,
                'codigo_sap': tracker.tracker_detail.tracker_detail.product.sap_code,
                'fecha_vencimiento': tracker.tracker_detail.expiration_date,
                'cantidad': tracker.quantity,
                'lote': tracker.lote.code if tracker.lote else None,
                # Tiempo en bodega en dias
                'time_in_warehouse': (tracker.created_at - tracker.tracker_detail.created_at).days
            })
        # asociar fechas de vencimiento de los tracker detail all a cada linea del excel segun el codigo sap y la cantidad si faltan cantidades tomar de los tracker detail all
        for index, row in df.iterrows():
            codigo_sap = row['Cod_Mat']
            # verificar si existe el producto en la lista de productos
            product = list(filter(lambda x: x['codigo_sap'] == str(codigo_sap), product_list))
            if len(product) == 0:
                product_list.append({
                    'codigo_sap': str(codigo_sap),
                    'nombre': row['Producto'].strip(),
                })
            client_id = list(filter(lambda x: x['nombre'] == row['Nombre'].strip(), client_ids))[0]['id']
            # omitir si el codigo sap empieza con 350
            if str(codigo_sap).startswith('350'):
                continue
            cantidad = row['Cant_UMV']
            # Buscar en la lista de data si existe el codigo sap y la cantidad es mayor a 0
            tracker_detail_product = list(filter(lambda x: x['codigo_sap'] == str(codigo_sap) and x['cantidad'] > 0, data))
            if len(tracker_detail_product) > 0:
                # si al hacer la resta la cantidad es menor a 0, romar del siguiente tracker detail product osea ambas fechas de vencimiento y tracker y restar la cantidad
                if cantidad > tracker_detail_product[0]['cantidad']:
                    if len(tracker_detail_product) > 1:

                        list_fecha_vencimiento = [ str(tracker_detail_product[0]['fecha_vencimiento']), str(tracker_detail_product[1]['fecha_vencimiento']) ]
                        list_tracker = [tracker_detail_product[0]['tracker_id'], tracker_detail_product[1]['tracker_id']]
                        list_lote = [tracker_detail_product[0]['lote'], tracker_detail_product[1]['lote']]

                        # guardar el dataframe
                        data_simulated.append({
                            'TOUR_ID': row['TOUR_ID'],
                            'Entrega': row['Entrega'],
                            'Población': row['Población'],
                            'Conductor': row['Conductor'],
                            'Calle': row['Calle'],
                            'Cod_Mat': row['Cod_Mat'],
                            'Producto': row['Producto'],
                            'Nombre': row['Nombre'],
                            'UM': row['UM'],
                            'Cant_UMV': cantidad,
                            'fecha_vencimiento': list_fecha_vencimiento,
                            'tracker': list_tracker,
                            'client_id': client_id,
                            'lote': list_lote,
                            'time_in_warehouse': tracker_detail_product[0]['time_in_warehouse'],
                        })
                        # restar la cantidad disponible del primer tracker detail product y el resto a la cantidad del segundo tracker detail product
                        cantididad_restante = cantidad - tracker_detail_product[0]['cantidad']
                        tracker_detail_product[0]['cantidad'] = 0
                        tracker_detail_product[1]['cantidad'] = tracker_detail_product[1]['cantidad'] - cantididad_restante
                        continue
                # guardar el dataframe
                data_simulated.append({
                    'TOUR_ID': row['TOUR_ID'],
                    'Entrega': row['Entrega'],
                    'Población': row['Población'],
                    'Conductor': row['Conductor'],
                    'Calle': row['Calle'],
                    'Cod_Mat': row['Cod_Mat'],
                    'Producto': row['Producto'],
                    'Nombre': row['Nombre'],
                    'UM': row['UM'],
                    'Cant_UMV': cantidad,
                    'fecha_vencimiento': str(tracker_detail_product[0]['fecha_vencimiento']),
                    'tracker': tracker_detail_product[0]['tracker_id'],
                    'client_id': client_id,
                    'lote': tracker_detail_product[0]['lote'],
                    'time_in_warehouse': tracker_detail_product[0]['time_in_warehouse'],

                })
                # restar la cantidad del tracker detail product
                tracker_detail_product[0]['cantidad'] = tracker_detail_product[0]['cantidad'] - cantidad


            else:
                row['fecha_vencimiento'] = None
                row['tracker_detail_product'] = None
                row['cantidad'] = 0

        # guardar la data simulada en la base de datos todo el json
        tour_id_list = tour_id_list.tolist()
        conductor_list = conductor_list.tolist()
        data = {
            'tour_id_list': tour_id_list,
            'conductor_list': conductor_list,
            'client_ids': client_ids,
            'product_list': product_list,
            'data': data_simulated
        }
        output.simulation = data
        output.save()

        return Response(data, status=status.HTTP_200_OK)



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
