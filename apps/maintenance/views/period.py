from rest_framework import viewsets, mixins
from ..models import PeriodModel, DistributorCenter
from ..serializer import PeriodModelSerializer, DistributorCenterSerializer
from apps.user.models import UserModel
from apps.user.serializers import UserSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.user.views.user import CustomAccessPermission
from rest_framework.exceptions import APIException
from apps.maintenance.exceptions.maintenance import NoDistributionCenterError, NoPeriodError
from datetime import date
class PeriodViewSet(mixins.ListModelMixin, 
                    mixins.RetrieveModelMixin, 
                    viewsets.GenericViewSet):
    queryset = PeriodModel.objects.all()
    serializer_class = PeriodModelSerializer
    permission_classes = [CustomAccessPermission]
    PERMISSION_MAPPING = {
        'GET': ['period.view_periodmodel'],
        'POST': ['period.add_periodmodel'],
        'PUT': ['period.change_periodmodel'],
        'PATCH': ['period.change_periodmodel'],
        'DELETE': ['period.delete_periodmodel'],
    }

    @action(detail=False, methods=['get'], url_path='last-period')
    def get_last_period(self, request, *args, **kwargs):
        user = request.user
        cd = user.centro_distribucion
        period = None
        if cd == None: 
            period = PeriodModel(label="A")
        periods = PeriodModel.objects.filter(distributor_center = cd).order_by('-initialDate')
        if periods.count() <= 0: 
            period = PeriodModel(label="A", distributor_center=cd)
        if period is None:
            period = periods[0]
        serializer = self.get_serializer(period)
        return Response(serializer.data, status=status.HTTP_200_OK)
 
