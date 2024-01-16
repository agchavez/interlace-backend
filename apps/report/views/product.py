import django_filters
from django.db.models import Sum, F
from rest_framework import viewsets
from datetime import date, timedelta
from rest_framework import serializers
from rest_framework.response import Response

from apps.tracker.models import TrackerDetailProductModel
from apps.maintenance.models import ProductModel, DistributorCenter
from apps.user.views.user import CustomAccessPermission
from utils.variable import not_input_product


class TrackerDetailProductSerializer(serializers.Serializer):
    product_name = serializers.CharField()
    sap_code = serializers.CharField()
    expiration_list = serializers.ListField()
    distributor_center = serializers.CharField()


class TrackerDetailProductFilter(django_filters.FilterSet):
    product = django_filters.ModelMultipleChoiceFilter(
        field_name='tracker_detail__product',
        to_field_name='id',
        queryset=ProductModel.objects.all()
    )
    productos = django_filters.CharFilter(
        method='filter_product_in'
    )
    distributor_center = django_filters.ModelMultipleChoiceFilter(
        field_name='tracker_detail__tracker__distributor_center',
        to_field_name='id',
        queryset=DistributorCenter.objects.all()
    )

    def filter_product_in(self, queryset, name, value):
        products = value.split(',')  # Assuming values are comma-separated
        return queryset.filter(tracker_detail__product__in=products)
    class Meta:
        model = TrackerDetailProductModel
        fields = []

class ProductosProximosAVencerAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrackerDetailProductSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = TrackerDetailProductFilter
    queryset = TrackerDetailProductModel.objects.all()
    permission_classes = [CustomAccessPermission]

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

    def get_queryset(self):
        fecha_actual = date.today()
        daysQuery = self.request.query_params.get('days', None)
        days = 60
        if daysQuery is not None:
            days = int(daysQuery)
        fecha_limite = fecha_actual + timedelta(days=days)

        queryset = (TrackerDetailProductModel.objects.filter(
            expiration_date__gte=fecha_actual,
            expiration_date__lte=fecha_limite,
            available_quantity__gt=0,
            tracker_detail__tracker__status='COMPLETE',
            tracker_detail__isnull=False,
        ).exclude(
            tracker_detail__product__sap_code__in=not_input_product
        ).values(
            'tracker_detail__product__name',
            'expiration_date',
            'quantity',
            'available_quantity',
            'tracker_detail__tracker__id',
            'tracker_detail__tracker__distributor_center__name',
            'tracker_detail__product__sap_code',

        ).annotate(
            product_name=F('tracker_detail__product__name'),
            sap_code=F('tracker_detail__product__sap_code'),
            distributor_center=F('tracker_detail__tracker__distributor_center__name'),
        ))

        queryset = queryset.order_by('expiration_date')


        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Diccionario para mantener un seguimiento de los productos
        productos_dict = {}

        # Agrupar por producto y construir el diccionario
        for item in queryset:
            producto = item['product_name']
            sap_code = item['sap_code']
            expiration_date = item['expiration_date']
            distributor_center = item['distributor_center']

            if producto not in productos_dict:
                productos_dict[producto] = {
                    'product_name': producto,
                    'sap_code': sap_code,
                    'expiration_list': [{
                        'expiration_date': expiration_date,
                        'quantity': item['quantity'],
                        'available_quantity': item['available_quantity'],
                        'tracker_id': item['tracker_detail__tracker__id'],
                    }],
                    'distributor_center': distributor_center,
                }
            else:
                productos_dict[producto]['expiration_list'].append({
                        'expiration_date': expiration_date,
                        'quantity': item['quantity'],
                        'available_quantity': item['available_quantity'],
                        'tracker_id': item['tracker_detail__tracker__id'],
                    })


        # Convertir el diccionario en una lista para la respuesta final
        lista_productos = list(productos_dict.values())

        # paginacion
        page = self.paginate_queryset(lista_productos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(lista_productos)

