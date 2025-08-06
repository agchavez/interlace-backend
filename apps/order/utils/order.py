from django.db import transaction

from ..exceptions.order_detail import LocationRequired, PermissionDenied
from ..models.detail import OrderDetailModel
from ..models.order import OrderModel
from ...inventory.models import InventoryMovementModel
from ...inventory.exceptions.inventory import FileRequired, InvalidFile, RequiredColumns
from ...maintenance.models import LocationModel
from ...tracker.models import TrackerDetailProductModel
from ...maintenance.models import ProductModel


# pandas
import pandas as pd

# validar y crear la order
@transaction.atomic
def validate_and_create_order(request):
    # validar si manda el excel, la localidad
    if not 'file' in request.FILES:
        raise FileRequired()
    if not 'location' in request.data:
        raise LocationRequired()
    else:
        location = request.data['location']
        try:
            localtion_instance = LocationModel.objects.get(id=location)
        except LocationModel.DoesNotExist:
            raise LocationRequired()

        # Validar que el archivo sea un excel y se pueda leer
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

    # FUNCIONALIDAD HÍBRIDA: Detectar formato del Excel
    # Formato con tracker: requiere 'tracker_id', 'codigo_sap', 'fecha_vencimiento', 'cantidad'
    # Formato directo: requiere 'codigo_sap', 'fecha_vencimiento', 'cantidad' (sin tracker_id)
    
    required_base_columns = ['codigo_sap', 'fecha_vencimiento', 'cantidad']
    has_tracker_column = 'tracker_id' in df.columns
    
    # Validar columnas requeridas
    missing_columns = [col for col in required_base_columns if col not in df.columns]
    if missing_columns:
        raise RequiredColumns()

    list_data = []
    list_data_error = []

    for index, row in df.iterrows():
        codigo_sap = row['codigo_sap']
        fecha_vencimiento = row['fecha_vencimiento'].strftime('%Y-%m-%d')
        cantidad = row['cantidad']
        
        # FUNCIONALIDAD HÍBRIDA: Procesar según el tipo de Excel
        if has_tracker_column and pd.notna(row['tracker_id']):
            # MODO TRACKER (funcionalidad original)
            tracker_id = row['tracker_id']
            try:
                tracker_detail_product = TrackerDetailProductModel.objects.get(
                    tracker_detail__tracker__id=tracker_id,
                    tracker_detail__product__sap_code=str(codigo_sap),
                    expiration_date=str(fecha_vencimiento),
                )

                if cantidad > tracker_detail_product.available_quantity or cantidad <= 0:
                    list_data_error.append({
                        "tracker_id": tracker_id,
                        "codigo_sap": codigo_sap,
                        "fecha_vencimiento": fecha_vencimiento,
                        "cantidad": cantidad,
                        "error": "Cantidad inválida o supera disponible en tracker"
                    })
                    continue

                data = {
                    "tracker_detail_product": tracker_detail_product,
                    "quantity": cantidad,
                    "quantity_available": cantidad,
                }

                list_data.append(data)

            except TrackerDetailProductModel.DoesNotExist:
                list_data_error.append({
                    "tracker_id": tracker_id,
                    "codigo_sap": codigo_sap,
                    "fecha_vencimiento": fecha_vencimiento,
                    "cantidad": cantidad,
                    "error": "Producto no encontrado en tracker"
                })
        else:
            # MODO DIRECTO (nueva funcionalidad híbrida)
            try:
                product = ProductModel.objects.get(sap_code=str(codigo_sap))
                
                if cantidad <= 0:
                    list_data_error.append({
                        "codigo_sap": codigo_sap,
                        "fecha_vencimiento": fecha_vencimiento,
                        "cantidad": cantidad,
                        "error": "Cantidad debe ser mayor a 0"
                    })
                    continue

                data = {
                    "product": product,
                    "distributor_center": cd,
                    "expiration_date": fecha_vencimiento,
                    "quantity": cantidad,
                    "quantity_available": cantidad,
                }

                list_data.append(data)

            except ProductModel.DoesNotExist:
                list_data_error.append({
                    "codigo_sap": codigo_sap,
                    "fecha_vencimiento": fecha_vencimiento,
                    "cantidad": cantidad,
                    "error": "Producto no encontrado por código SAP"
                })

    # crear la orden
    order = OrderModel.objects.create(
        location=localtion_instance,
        observations=observations,
        distributor_center=cd,
        user=request.user,
    )
    order.save()

    # crear los detalles de la orden
    for item in list_data:
        item['order'] = order
        OrderDetailModel.objects.create(**item)

    return (order, list_data_error)


# insertar los detalles de la orden a movimiento de inventario cuando se completa la orden
@transaction.atomic
def insert_order_detail_to_inventory_movement(order, user_id):
    # obtener los detalles de la orden
    order_detail = OrderDetailModel.objects.filter(order=order)
    # recorrer los detalles de la orden
    for item in order_detail:
        # FUNCIONALIDAD HÍBRIDA: Solo procesar productos con tracker_detail_product
        # Los productos directos no se registran en movimientos de inventario
        if item.tracker_detail_product:
            # crear el movimiento de inventario
            InventoryMovementModel.objects.create(
                tracker_detail_product=item.tracker_detail_product,
                quantity=item.quantity * -1,
                movement_type=InventoryMovementModel.MovementType.OUT,
                module=InventoryMovementModel.Module.ORDER,
                origin_id=order.id,
                user_id=user_id,
            )

        # quantity_available de order detail = 0 (para ambos tipos)
        item.quantity_available = 0
        item.save()

