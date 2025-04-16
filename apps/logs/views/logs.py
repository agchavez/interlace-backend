
from datetime import datetime
from rest_framework import viewsets, response
from rest_framework import filters as rest_filters
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from ..models import LogActionModel, LogControlModel
from ..serializers import LogActionSerializer, LogControlSerializer

from ...user.models import UserModel
from ...user.views.user import CustomAccessPermission


class LogControlFilter(filters.FilterSet):
    action = filters.ModelMultipleChoiceFilter(
        queryset=LogActionModel.objects.all(),
        field_name='action',
    )
    user = filters.ModelMultipleChoiceFilter(
        queryset=UserModel.objects.all(),
        field_name='user',
    )
    model = filters.MultipleChoiceFilter(
        choices=LogActionModel.Modules.choices,
        field_name='action__module',
    )
    action_type = filters.MultipleChoiceFilter(
        choices=LogActionModel.ActionTypes.choices,
        field_name='action__action',
    )

    start_date = filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
    )
    end_date = filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
    )
    id_register = filters.NumberFilter(
        field_name='id_register',
    )

    class Meta:
        model = LogControlModel
        fields = ['action', 'user', 'model', 'action_type', 'start_date', 'end_date', 'id_register']

class LogActionView(viewsets.ModelViewSet):
    permission_classes = [CustomAccessPermission]
    queryset = LogActionModel.objects.all()
    serializer_class = LogActionSerializer
    filter_backends = [filters.DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_fields = ['id']
    search_fields = ['name', 'description', 'action']
    ordering = ['-id']


    PERMISSION_MAPPING = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': [],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

class LogControlView(viewsets.ModelViewSet):    
    permission_classes = [CustomAccessPermission]
    queryset = LogControlModel.objects.all()
    serializer_class = LogControlSerializer
    filter_backends = [filters.DjangoFilterBackend, rest_filters.SearchFilter, OrderingFilter,]
    search_fields = ['user__first_name', 'user__last_name','action__name', 'action__action', 'action__description']
    ordering = ['-id']
    filterset_class = LogControlFilter

    PERMISSION_MAPPING = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': [],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])


    def convert_to_datetime(self,date_string):
        date_object = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
        fecha = date_object.strftime('%Y-%m-%d %H:%M:%S.%f').lower() 
        return fecha