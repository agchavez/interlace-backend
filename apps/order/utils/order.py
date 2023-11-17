from django.db import transaction

from ..exceptions.order_detail import LocationRequired, PermissionDenied
from ..models.detail import OrderDetailModel
from ..models.order import OrderModel
from ...inventory.exceptions.inventory import FileRequired, InvalidFile, RequiredColumns
from ...maintenance.models import LocationModel
from ...tracker.models import TrackerDetailProductModel


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

    if not 'tracker_id' in df.columns or not 'codigo_sap' in df.columns or not 'fecha_vencimiento' in df.columns or not 'cantidad' in df.columns:
        raise RequiredColumns()

    list_data = []
    list_data_error = []

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
