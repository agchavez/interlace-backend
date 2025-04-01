import django_filters

from apps.maintenance.models import TrailerModel, TransporterModel, DistributorCenter
from apps.tracker.models import TrackerModel, TrackerDetailProductModel
from apps.user.models import UserModel as User

class TrackerFilter(django_filters.FilterSet):
    transporter = django_filters.ModelMultipleChoiceFilter(
        queryset=TransporterModel.objects.all(),
        field_name='transporter__id',
        to_field_name='id'
    )
    trailer = django_filters.ModelMultipleChoiceFilter(
        queryset=TrailerModel.objects.all(),
        field_name='trailer__id',
        to_field_name='id'
    )
    user = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name='user__id',
        to_field_name='id'
    )

    date = django_filters.DateFromToRangeFilter(
        field_name='created_at',
        label='Fecha de creación'
    )

    distributor_center = django_filters.ModelMultipleChoiceFilter(
        queryset=DistributorCenter.objects.all(),
        field_name='distributor_center__id',
        to_field_name='id'
    )

    id = django_filters.NumberFilter(
        field_name='id',
        label='ID'
    )

    status = django_filters.CharFilter(
        field_name='status',
        label='Status',
        method='filter_status',
    )

    def filter_status(self, queryset, name, value):
        values = value.split(',')
        return queryset.filter(status__in=values)

    class Meta:
        model = TrackerModel
        fields = ('transporter', 'trailer', 'status','type', 'user', 'date', 'distributor_center', 'id')

class TrackerDetailProductModelFilter(django_filters.FilterSet):
        order_by = django_filters.OrderingFilter(
            fields=(
                ('created_at', 'created_at')
            )
        )

        class Meta:
            model = TrackerDetailProductModel
            fields = {
                'tracker_detail': ['exact'],
                'tracker_detail__tracker': ['exact'],
                'tracker_detail__tracker__distributor_center': ['exact'],
                'tracker_detail__product': ['exact'],
                'created_at': ['gte', 'lte'],
                'expiration_date': ['gte', 'lte', 'exact'],
                'id': ['exact'],
                'tracker_detail__tracker__status': ['exact'],
                'tracker_detail__tracker__user': ['exact'],
                'available_quantity': ['gt', 'lt', 'exact'],

            }
