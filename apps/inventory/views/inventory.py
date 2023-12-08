
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
# decorador y respuestas 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet

from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from ..exceptions.inventory import ReasonRequired, FileRequired, InvalidFile, RequiredColumns
from ..models import InventoryMovementModel
from ..serializers import InventoryMovementSerializer, InventoryMovementMassiveSerializer 
import pandas as pd  # Asegúrate de tener instalada la librería pandas

from ...tracker.models import TrackerDetailProductModel
from ...user.views.user import CustomAccessPermission


# Filtros de movimientos de inventario
class InventoryMovementFilter(filters.FilterSet):
    class Meta:
        model = InventoryMovementModel
        fields = {
            'movement_type': ['exact'],
            'user': ['exact'],
            'tracker_detail_product__tracker_detail__tracker__distributor_center': ['exact'],
            'tracker_detail_product__tracker_detail__product': ['exact'],
            'tracker_detail_product__tracker_detail__product__sap_code': ['exact'],
            'tracker_detail_product__tracker_detail__product__name': ['contains'],
            'module': ['exact'],
            'origin_id': ['exact'],
            'is_applied': ['exact'],
        }
# Vista de movimientos de inventario
class InventoryMovementViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = InventoryMovementModel.objects.all()
    serializer_class = InventoryMovementSerializer
    filterset_class = InventoryMovementFilter
    filter_backends = [DjangoFilterBackend]

    permission_classes = [CustomAccessPermission]
    PERMISSION_MAPPING = {
        'GET': ['inventory.view_inventorymovementmodel'],
        'POST': ['inventory.add_inventorymovementmodel'],
        'PUT': ['inventory.change_inventorymovementmodel'],
        'PATCH': ['inventory.change_inventorymovementmodel'],
        'DELETE': ['inventory.delete_inventorymovementmodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])


    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        serializer = InventoryMovementMassiveSerializer(data=request.data)
        list_data = []
        if serializer.is_valid():
            movements_data = serializer.validated_data['list']
            reason = serializer.validated_data['reason']
            type = InventoryMovementModel.MovementType.BALANCE
            last_balance_movement = InventoryMovementModel.objects.filter(movement_type=type).order_by(
                '-origin_id').first()

            if last_balance_movement:
                last_origin_id = last_balance_movement.origin_id
                new_origin_id = last_origin_id + 1
            else:
                # Si no hay movimientos de balance anteriores, puedes asignar el valor inicial que desees.
                new_origin_id = 1
            # Realizar la lógica para crear movimientos de inventario masivos
            for movement_data in movements_data:
                data = {
                    "origin_id": new_origin_id,
                    "tracker_detail_product_id": movement_data['tracking_detail_product'],
                    "quantity": movement_data['quantity'],
                    "module": InventoryMovementModel.Module.ADMIN,
                    "movement_type": type,
                    "reason": reason,
                    "user_id": 1
                }
                new_inv = InventoryMovementModel.objects.create(**data)
                new_inv.save()
                list_data.append(InventoryMovementSerializer(new_inv).data)
            # Aquí deberías extraer la información necesaria y crear instancias de InventoryMovementModel
            # ...

            # Retornar una respuesta exitosa
            return Response({
                'ok': 'Movimientos masivos creados correctamente.',
                'data': list_data
            }, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # Carga masiva por excel
    @action(detail=False, methods=['post'], url_path='batch-create-excel')
    def batch_create_excel(self, request):
        if not 'reason' in request.data:
            raise ReasonRequired()
        if not 'file' in request.FILES:
            raise FileRequired()
        file = request.FILES.get('file')
        reason = request.data['reason']
        if not reason or reason == '':
            raise  ReasonRequired()

        # Validar que el archivo sea un excel y se pueda leer
        if not file.name.endswith('.xlsx'):
            raise InvalidFile()

        df = pd.read_excel(file)

        if not 'tracker_id' in df.columns or not 'codigo_sap' in df.columns or not 'fecha_vencimiento' in df.columns or not 'cantidad' in df.columns:
            raise RequiredColumns()

        list_data = []
        list_data_error = []
        type = InventoryMovementModel.MovementType.BALANCE
        last_balance_movement = InventoryMovementModel.objects.filter(movement_type=type).order_by(
            '-origin_id').first()

        if last_balance_movement:
            last_origin_id = last_balance_movement.origin_id
            new_origin_id = last_origin_id + 1
        else:
            new_origin_id = 1

        # Lógica para crear movimientos de inventario masivos desde el archivo Excel
        for index, row in df.iterrows():
            tracker_id = row['tracker_id']
            codigo_sap = row['codigo_sap']
            fecha_vencimiento = row['fecha_vencimiento'].strftime('%Y-%m-%d')
            cantidad = row['cantidad']

            try:
                tracker_detail_product = TrackerDetailProductModel.objects.get(
                    tracker_detail__tracker__id=tracker_id,
                    tracker_detail__product__sap_code=str(codigo_sap),
                    expiration_date=str(fecha_vencimiento),
                )
                data = {
                    "origin_id": new_origin_id,
                    "tracker_detail_product_id": tracker_detail_product.id,
                    "quantity": cantidad,
                    "module": InventoryMovementModel.Module.ADMIN,
                    "movement_type": type,
                    "reason": reason,
                    "user_id": request.user.id
                }
                new_inv = InventoryMovementModel.objects.create(**data)
                new_inv.save()
                list_data.append(InventoryMovementSerializer(new_inv).data)

            except TrackerDetailProductModel.DoesNotExist:
                list_data_error.append({
                    "tracker_id": tracker_id,
                    "codigo_sap": codigo_sap,
                    "fecha_vencimiento": fecha_vencimiento,
                    "cantidad": cantidad,
                    "error": "No existe registro con estos datos.",
                })
        # Retornar una respuesta exitosa
        return Response({
            'data': list_data,
            'data_error': list_data_error
        }, status=HTTP_200_OK)
    


