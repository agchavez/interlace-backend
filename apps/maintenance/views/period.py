from rest_framework import viewsets, mixins
from ..models import PeriodModel, DistributorCenter, ProductModel
from ..serializer import PeriodModelSerializer, DistributorCenterSerializer
from apps.user.models import UserModel
from apps.user.serializers import UserSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.user.views.user import CustomAccessPermission
from rest_framework.exceptions import APIException
from apps.maintenance.exceptions.maintenance import NoProductError, ProductNoIntegerError
from datetime import date
import pandas as pd

class PeriodViewSet(mixins.ListModelMixin, 
                    mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    queryset = PeriodModel.objects.all()
    serializer_class = PeriodModelSerializer
    permission_classes = []
    PERMISSION_MAPPING = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': [],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    
    @action(detail=False, methods=['get'], url_path='last-period')
    def get_last_period(self, request, *args, **kwargs):
        user = request.user
        cd = user.centro_distribucion
        product_param = request.query_params.get('product')
        print("product", product_param)
        if product_param == None:
            raise NoProductError()
        try:
            product_param = int(product_param)
        except ValueError:
            raise ProductNoIntegerError()
        period = None
        if cd == None: 
            period = PeriodModel(label="A")
        periods = PeriodModel.objects.filter(distributor_center = cd, product=product_param).order_by('-initialDate')
        if periods.count() <= 0: 
            period = PeriodModel(label="A", distributor_center=cd)
        if period is None:
            period = periods[0]
        serializer = self.get_serializer(period)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # carga masiva de periodos
    @action(detail=False, methods=['post'], url_path='load-excel')
    def load_excel(self, request):
        file = request.data.get('file')
        if file is None:
            raise APIException("No file found")
        df = pd.read_excel(file)
        # tiene que existir las columnas: centro_distribucion, producto, fecha_inicial, label
        if 'centro_distribucion' not in df.columns or 'producto' not in df.columns or 'fecha_inicial' not in df.columns or 'label' not in df.columns:
            raise APIException("Columns not found")
        for index, row in df.iterrows():
            distributor_center = row['centro_distribucion']
            product = row['producto']
            initialDate = row['fecha_inicial']
            label = row['label']
            if ProductModel.objects.filter(id=product).count() <= 0:
                continue
            PeriodModel.objects.create(
                distributor_center_id=distributor_center,
                product_id=product,
                initialDate=initialDate,
                label=label
            )

        return Response({
            'message': 'File loaded'
        }, status=status.HTTP_201_CREATED)
 
