from datetime import datetime

import openpyxl
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

from ..filters import TrackerFilter, TrackerDetailProductModelFilter
# Models
from ..models import TrackerModel, TrackerDetailModel, TrackerDetailProductModel, TrackerOutputT2Model
# Serializers
from ..serializers import TrackerSerializer, TrackerDetailModelSerializer, TrackerDetailProductModelSerializer
from apps.maintenance.models import ProductModel, PeriodModel

from apps.tracker.exceptions.tracker import TrackerCompleted, UserWithoutDistributorCenter, TrackerCompletedDetail, \
    TrackerCompletedDetailProduct, FileTooLarge, FileNotExists, ProductIdRequired

from apps.user.views.user import CustomAccessPermission
from apps.tracker.models import TrackerDetailOutputModel
from rest_framework.filters import OrderingFilter
from django.http import HttpResponse
from ..utils.processes import apply_output_movements
from ..utils.validate_tracker import validate_complete_tracker, validate_create_tracker
from ...document.utils.documents import create_documento
from ...order.utils.update import update_order_detail




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
    #         return TrackerModel.objects.filter(distributdashor_center=user.centro_distribucion)
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

    def list(self, request, *args, **kwargs):
        # agregar filtro adicional
        queryset = self.filter_queryset(self.get_queryset())

        user = request.user

        # try:
        #     if user.centro_distribucion:
        #         queryset = queryset.filter(distributor_center=user.centro_distribucion)
        # except:
        #     pass

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
            apply_output_movements.delay(tracker.id, request.user.id)


        tracker.complete()

        # si el time invested es 10 minutos superior al promedio del mes, se excluye del TAT
        # verificar si hay trackers completados
        if TrackerModel.objects.filter(status='COMPLETE', distributor_center=tracker.distributor_center).count() > 0:
            tat_average = (TrackerModel.objects.filter(status='COMPLETE', distributor_center=tracker.distributor_center, exclude_tat=False)
                           .aggregate(Sum('time_invested')))
            tat_average = tat_average.get('time_invested__sum') / TrackerModel.objects.filter(status='COMPLETE', distributor_center=tracker.distributor_center, exclude_tat=False).count()
            if tracker.time_invested > tat_average + 600:
                tracker.exclude_tat = True
                tracker.save()
            # la fecha de completado se actualiza en el modelo
            tracker.completed_date = datetime.now()
            tracker.save()

        # aplicar movimientos de salida
        return Response({'detail': 'Se completo el tracker'}, status=status.HTTP_200_OK)

    # Información del dashboard por centro de distribucion de usuarios
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
        tracker_average_complete = queryset.filter(status='COMPLETE', exclude_tat=False).count()
        time_average = queryset.filter(status='COMPLETE', exclude_tat=False).aggregate(Sum('time_invested'))
        # Tiempo promedio en completar un tracker
        time_average = time_average.get('time_invested__sum') / tracker_average_complete if tracker_average_complete > 0 else 0
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

        # Detectar qué archivos se envían y qué operación realizar para cada uno
        file_1 = request.FILES.get("file_1")
        file_2 = request.FILES.get("file_2")

        # Campo para identificar qué archivo eliminar (si corresponde)
        delete_file_1 = request.data.get("delete_file_1") == "true"
        delete_file_2 = request.data.get("delete_file_2") == "true"

        # Procesar file_1
        if file_1 is not None:
            if file_1.size > 20 * 1024 * 1024:
                raise FileTooLarge
            # Crear documento para file_1
            document_1 = create_documento(
                file_1,
                name=file_1.name,
                folder="Tracker",
                subfolder=str(tracker.id)
            )
            tracker.file_1 = document_1
        elif delete_file_1:
            tracker.file_1 = None

        # Procesar file_2
        if file_2 is not None:
            if file_2.size > 20 * 1024 * 1024:
                raise FileTooLarge
            # Crear documento para file_2
            document_2 = create_documento(
                file_2,
                name=file_2.name,
                folder="Tracker",
                subfolder=str(tracker.id)
            )
            tracker.file_2 = document_2
        elif delete_file_2:
            tracker.file_2 = None

        # Guardar cambios
        tracker.save()

        # Devolver datos actualizados
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

    @action(detail=False, methods=['get'], url_path='report')
    def getReport(self, request, *args, **kwargs):
        # Obtener los parámetros de fecha
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')

        if not date_start or not date_end:
            return Response({'error': 'Los parámetros date_start y date_end son obligatorios.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'El formato de las fechas debe ser YYYY-MM-DD.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Filtrar trackers por rango de fechas
        trackers = TrackerModel.objects.filter(
            created_at__date__gte=date_start, created_at__date__lte=date_end
        ).select_related(
            'distributor_center', 'origin_location', 'destination_location', 'operator_1', 'operator_2', 'trailer',
        ).prefetch_related(
            'tracker_detail__tracker_product_detail', 'tracker_detail__product'
        )

        distributor_centers = trackers.values_list('distributor_center', flat=True).distinct()
        products = TrackerDetailModel.objects.filter(tracker__in=trackers).values_list('product', flat=True).distinct()
        periods = PeriodModel.objects.filter(
            distributor_center__in=distributor_centers,
            product__in=products
        ).order_by('-initialDate')

        # Crear un diccionario para acceder rápidamente a los periodos
        period_dict = {}
        for period in periods:
            key = (period.distributor_center_id, period.product_id)
            if key not in period_dict or period.initialDate > period_dict[key].initialDate:
                period_dict[key] = period

        # Crear el archivo Excel
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Reporte de Trackers'

        # Encabezados
        headers = [
            'ID Tracker', 'Número de Placa', 'Número de Documento de Entrada', 'Número de Documento de Salida',
            'Número de Traslado', 'Contabilizado', 'Operador 1', 'Operador 2', 'Estado', 'Tipo',
            'Fecha de Creación', 'Centro de Distribución', 'Localidad Origen', 'Código Localidad Origen',
            'Localidad Destino', 'Código Localidad Destino', 'Código SAP', 'Producto', 'Cantidad', 'Fecha de Vencimiento',
            'Cantidad Disponible', 'Observación', 'TAT', 'Fecha Completado', 'Giro', 'Turno', 'Unidad de descarga'
        ]
        sheet.append(headers)

        # Agregar datos al Excel
        for tracker in trackers:
            created_hour = tracker.created_at.hour + (tracker.created_at.minute / 60.0)
            if 6 <= created_hour <= 14:
                shift = 'A'
            elif 14 < created_hour <= 22:
                shift = 'B'
            else:  # 22 < created_hour < 24 or 0 <= created_hour < 6
                shift = 'C'
            for detail in tracker.tracker_detail.all():
                for product_detail in detail.tracker_product_detail.all():

                    key = (tracker.distributor_center_id, detail.product_id)
                    period = period_dict.get(key)
                    giro = period.label if period else 'N/A'

                    # Formatear fechas directamente sin ajustes de zona horaria
                    # Acceder a los valores raw de la base de datos para evitar conversiones automáticas
                    created_at_formatted = tracker.created_at.strftime('%d/%m/%Y %H:%M:%S') if tracker.created_at else 'N/A'
                    completed_date_formatted = tracker.completed_date.strftime('%d/%m/%Y %H:%M:%S') if tracker.completed_date else 'N/A'
                    expiration_date_formatted = product_detail.expiration_date.strftime(
                        '%d/%m/%Y') if product_detail.expiration_date else 'N/A'

                    sheet.append([
                        tracker.id,
                        tracker.plate_number or 'N/A',
                        tracker.input_document_number or 'N/A',
                        tracker.output_document_number or 'N/A',
                        tracker.transfer_number or 'N/A',
                        tracker.accounted or 'N/A',
                        tracker.operator_1.get_full_name() if tracker.operator_1 else 'N/A',
                        tracker.operator_2.get_full_name() if tracker.operator_2 else 'N/A',
                        tracker.status,
                        tracker.type,
                        created_at_formatted,
                        tracker.distributor_center.name if tracker.distributor_center else 'N/A',
                        tracker.origin_location.name if tracker.origin_location else 'N/A',
                        tracker.origin_location.code if tracker.origin_location else 'N/A',
                        tracker.destination_location.name if tracker.destination_location else 'N/A',
                        tracker.destination_location.code if tracker.destination_location else 'N/A',
                        detail.product.sap_code if detail.product else 'N/A',
                        detail.product.name if detail.product else 'N/A',
                        detail.quantity,
                        expiration_date_formatted,
                        product_detail.available_quantity,
                        tracker.observation or 'N/A',
                        (tracker.time_invested // 60) if tracker.time_invested else 'N/A',
                        completed_date_formatted,
                        giro,
                        shift,
                        tracker.trailer.code,
                    ])

        # Configurar la respuesta HTTP para descargar el archivo
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_trackers.xlsx"'
        workbook.save(response)
        return response

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

        # if user is not isinstance(user, AnonymousUser) and hasattr(user, 'centro_distribucion'):
        #     if user.centro_distribucion:
        #         queryset = queryset.filter(tracker_detail__tracker__distributor_center=user.centro_distribucion)

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

    # Listar fechas disponibles por producto que su cantidad sea mayor a 0
    @action(detail=False, methods=['get'], url_path='available-dates')
    def available_dates(self, request, *args, **kwargs):
        # el id del producto es requerido
        product_id = request.GET.get('product_id')
        output_id = request.GET.get('output_id')
        if product_id is None or not product_id.isnumeric() or output_id is None or not output_id.isnumeric():
            raise ProductIdRequired()

        query = TrackerDetailProductModel.objects.filter(tracker_detail__product__id=product_id, available_quantity__gt=0)

        # ademas no tienen que estar ya seleccionadas en otras TrackerOutputT2Model restando las cantidades
# de los TrackerDetailProductModel

        # agrupar por fecha y sumar la cantidad disponible
        data = []
        for item in query.values('expiration_date').annotate(total=Sum('available_quantity')):
            data.append({
                'expiration_date': item.get('expiration_date'),
                'total': item.get('total'),
                'details': query.filter(expiration_date=item.get('expiration_date'))
                    .values('id', 'available_quantity')
                    # cambiar el nombre de las llaves
                    .annotate(tracker_id=F('tracker_detail__tracker__id'))
            })
        process_data = []
        for track in data:
            total = 0
            for detail in track['details']:
                if TrackerOutputT2Model.objects.filter(tracker_detail_id=detail['id'] ).exclude(output_detail__id=output_id).exists():
                    sum_quantity = (TrackerOutputT2Model.objects.filter(tracker_detail_id=detail['id'] ).exclude(output_detail__id=output_id).aggregate(Sum('quantity')))
                    if sum_quantity.get('quantity__sum') is None:
                        sum_quantity = {'quantity__sum': 0}
                    value = sum_quantity.get('quantity__sum')
                    if value is not None :
                        # si es igual a la cantidad disponible, eliminar el detalle
                        if value == detail['available_quantity']:
                            detail['available_quantity'] = 0
                        else:
                            detail['available_quantity'] = detail['available_quantity'] - value
                            total += detail['available_quantity']
                    else:
                        total += detail['available_quantity']
                else:
                    total += detail['available_quantity']
            if total > 0:
                track['total'] = total
                process_data.append(track)
        # ordenar por fecha de vencimiento mas reciente de primero
        process_data.sort(key=lambda x: x['expiration_date'], reverse=False)
        # paginar
        page = self.paginate_queryset(process_data)
        if page is not None:
            return self.get_paginated_response(process_data)

        return Response(process_data)

    def destroy(self, request, *args, **kwargs):
        if self.get_object().tracker_detail.tracker.status == 'COMPLETE':
            raise TrackerCompletedDetailProduct()
        return super().destroy(request, *args, **kwargs) 


