import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum
from celery import shared_task
from rest_framework import status

from ..models import OutputDetailT2Model, OutputT2Model, TrackerOutputT2Model
from ...inventory.exceptions.inventory import FileRequired, InvalidFile, RequiredColumns
from ...maintenance.models import ProductModel
from ...order.exceptions.order_detail import PermissionDenied

from helpers.mail import create_mail
import os

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

    if not 'pre_sale_date' in request.data:
        raise RequiredColumns()

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
            pre_sale_date=request.data.get('pre_sale_date'),
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


# tarea asincrona que hace la simulacion de la salida y envia correo al usuario
@shared_task
def simulate_output_t2(pd_records, output_id, data_email):
    try:
        df = pd.DataFrame(pd_records)
        # limpitar data eliminar filas vacias, cantidad = 0, cod_mat = 0 y todas las rutas que no sean la ruta seleccionada, Cod_Mat que empiecen con 350
        df = df.dropna()
        df = df[df['Cant_UMV'] != 0]
        df = df[df['Cod_Mat'] != 0]
        # Ordenear primeras rutas del conductor osea primero las primera ruta de los conductores y luego las segunda ruta de los conductores yu asi sucesivamente
        df = df.sort_values(by=['Conductor', 'TOUR_ID'], ascending=True)
        # codigo de sap del producto que coincide con 17365
        # df = df[df['Cod_Mat'].astype(str).str.startswith(producto)]

        df = df[~df['Cod_Mat'].astype(str).str.startswith('350')]

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
        tracker_detail_all = TrackerOutputT2Model.objects.filter(output_detail__output_id=output_id)
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
                        list_fecha_vencimiento = [str(tracker_detail_product[0]['fecha_vencimiento']),
                                                  str(tracker_detail_product[1]['fecha_vencimiento'])]
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
        output = OutputT2Model.objects.get(id=output_id)
        output.simulation = data
        output.save()

        # enviar correo de salida t2
        restore_password_notification(data_email)
        return True, 'Se ha realizado la simulacion de la salida T2'
    except Exception as e:
        return False, str(e)

def restore_password_notification(data):
    try:
        return create_mail(data['email'], "Simulacion salida T2", 'mails/simulate_complete.html', {
            'id': 'T2OUT-%s' % data['id'],
            'name': data['name'],
            'url': '%s%s%s' % (os.getenv('FRONTEND_URL'), '/tracker-t2/simulated/', data['id'])
        })
        print('Se envio el correo de salida T2')

    except Exception as e:
        print('Error al enviar el correo de salida T2' + str(e))

# enviar correo de salida t2
