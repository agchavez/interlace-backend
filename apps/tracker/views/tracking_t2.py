# rest_framework
import pandas as pd
from django.db.models import Sum
from rest_framework import viewsets, mixins, status

# transactions
from django.db import transaction

# actions
from rest_framework.decorators import action

# django filters
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from ..exceptions.tracker_t2 import DeleteStateCreated
from ..models import OutputT2Model, OutputDetailT2Model, TrackerOutputT2Model
from ..serializers import OutputDetailT2Serializer, TrackerOutputT2Serializer, OutputT2Serializer, \
    OutputTrackerT2MassiveSerializer
from ...inventory.exceptions.inventory import FileRequired, InvalidFile, RequiredColumns
from ...maintenance.models import ProductModel
from ...order.exceptions.order_detail import PermissionDenied
from ...user.views.user import CustomAccessPermission


class OutputT2FilterSet(django_filters.FilterSet):
    class Meta:
        model = OutputT2Model
        # rango de created_at
        fields = {
            'distributor_center': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
            'status': ['exact'],
        }


class OutputT2View(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                   mixins.DestroyModelMixin):
    queryset = OutputT2Model.objects.all()
    serializer_class = OutputT2Serializer
    permission_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_class = OutputT2FilterSet
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
        # validar si manda el excel, la localidad
        if not 'file' in request.FILES:
            raise FileRequired()
        file = request.FILES.get('file')
        if not file.name.endswith('.xlsx'):
            raise InvalidFile()

        try:
            cd = request.user.centro_distribucion
        except:
            raise PermissionDenied()
        location = request.data.get('location')
        observations = request.data.get('observations') if 'observations' in request.data else None
        # leer el excel
        df = pd.read_excel(file)

        if not 'Material' in df.columns or not 'Descripcion' in df.columns or not 'Total Disponible' in df.columns or not 'Cantidad en Pedidos' in df.columns:
            raise RequiredColumns()

        list_data = []
        list_data_error = []

        # Validar que los campos sean numericos tanto 'Material', 'Total Disponible' y 'Cantidad en Pedidos'
        df['Material'] = pd.to_numeric(df['Material'], errors='coerce')
        df['Total Disponible'] = pd.to_numeric(df['Total Disponible'], errors='coerce')
        df['Cantidad en Pedidos'] = pd.to_numeric(df['Cantidad en Pedidos'], errors='coerce')

        if df['Material'].isnull().values.any() or df['Total Disponible'].isnull().values.any() or df[
            'Cantidad en Pedidos'].isnull().values.any():
            raise RequiredColumns()
        products_list = []
        # validar que los productos existan en el inventario
        for index, row in df.iterrows():
            product = ProductModel.objects.filter(sap_code=row['Material'])
            if not product:
                list_data_error.append({
                    'product': row['Material'],
                    'quantity': row['Cantidad en Pedidos'],
                    'error': 'Producto no encontrado'
                })
            continue
        if list_data_error:
            return Response({
                'errors': list_data_error,
            }, status=status.HTTP_400_BAD_REQUEST)

        # restar total disponible - cantidad en pedidos y si es mayor a 0, agregar a la lista 'Cantidad en Pedidos' de lo contrario agregar 'Total Disponible'

        for index, row in df.iterrows():
            product = ProductModel.objects.get(sap_code=row['Material'])
            if row['Total Disponible'] - row['Cantidad en Pedidos'] > 0:
                list_data.append({
                    'product': product.id,
                    'quantity': row['Cantidad en Pedidos']
                })
            else:
                list_data.append({
                    'product': product.id,
                    'quantity': row['Total Disponible']
                })

        # crear la salida
        with transaction.atomic():
            output = OutputT2Model.objects.create(
                distributor_center=cd,
                observations=observations,
                user=request.user,
            )
            output.save()
            for data in list_data:
                # crear el detalle de la salida
                OutputDetailT2Model.objects.create(
                    output=output,
                    product_id=data['product'],
                    quantity=data['quantity']
                )
        return Response({
            'output': OutputT2Serializer(output).data,
            'output_detail': OutputDetailT2Serializer(OutputDetailT2Model.objects.filter(output=output),
                                                      many=True).data,
            'errors': list_data_error,
        }, status=status.HTTP_201_CREATED)

    # solo se puede eliminar si no tiene detalle de salida y el status es CREATED
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'CREATED':
            raise DeleteStateCreated()
        # if TrackerOutputT2Model.objects.filter(output_detail__output=instance).exists():
        #     return Response({
        #         'error': 'No se puede eliminar la salida'
        #     }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    permission_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_class = OutputDetailT2FilterSet
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
    permission_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_class = TrackerOutputT2FilterSet
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
