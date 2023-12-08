import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum
from rest_framework import status

from ..models import OutputDetailT2Model, OutputT2Model
from ...inventory.exceptions.inventory import FileRequired, InvalidFile, RequiredColumns
from ...maintenance.models import ProductModel
from ...order.exceptions.order_detail import PermissionDenied


def create_output_t2(request):
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
            # eliminar los productos que no existan en el inventario
            df.drop(index, inplace=True)


    # restar total disponible - cantidad en pedidos y si es mayor a 0, agregar a la lista 'Cantidad en Pedidos' de lo contrario agregar 'Total Disponible'

    for index, row in df.iterrows():
        # Si el Total disoponible o Cantidad en pedidos es menor o igual a 0, omitir el registro
        if row['Total Disponible'] <= 0 or row['Cantidad en Pedidos'] <= 0:
            continue
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
    data = {}
    # crear la salida
    with transaction.atomic():
        output = OutputT2Model.objects.create(
            distributor_center=cd,
            observations=observations,
            user=request.user,
        )
        output.save()
        data['output'] = output
        for data in list_data:
            # crear el detalle de la salida
            OutputDetailT2Model.objects.create(
                output=output,
                product_id=data['product'],
                quantity=data['quantity']
            )
    return output, status.HTTP_201_CREATED
