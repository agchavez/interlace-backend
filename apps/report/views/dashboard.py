from click.core import F
from django.db.models import Avg, Sum
from rest_framework import viewsets
from datetime import date, timedelta
from rest_framework import serializers
from rest_framework.response import Response

from apps.maintenance.models import PeriodModel
from apps.tracker.models.tracker import TrackerModel, TrackerDetailModel



# dashboard para los cds asignados al usuario
class DashboardSerializer(serializers.Serializer):
    # rango de fechas 'hoy', 'esta semana', 'este mes', 'este año'
    date_range = serializers.CharField(required=False)
    def validate(self, attrs):
        # si no se envia el rango de fechas se toma 'hoy'
        if not attrs.get('date_range'):
            attrs['date_range'] = 'today'
        else :
            if attrs.get('date_range') not in ['today', 'this_week', 'this_month', 'this_year']:
                raise serializers.ValidationError('Rango de fechas invalido')
        return attrs


class DashboardAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = DashboardSerializer
    permission_classes = []

    PERMISSION_MAPPING = {
        'GET': ['tracker.view_trackermodel'],
        'POST': ['tracker.add_trackermodel'],
        'PUT': ['tracker.change_trackermodel'],
        'PATCH': ['tracker.change_trackermodel'],
        'DELETE': ['tracker.delete_trackermodel'],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    def get_queryset(self):
        return TrackerModel.objects.all()

    def list(self, request, *args, **kwargs):
        resp = []
        cds = request.user.distributions_centers.all()

        if len(cds) > 1:
            if request.query_params.get('date_range') == 'today':
                trackers = TrackerModel.objects.filter(distributor_center__in=cds, created_at__date=date.today())
            elif request.query_params.get('date_range') == 'this_week':
                trackers = TrackerModel.objects.filter(distributor_center__in=cds, created_at__date__range=[
                    date.today() - timedelta(days=date.today().weekday()), date.today()])
            elif request.query_params.get('date_range') == 'this_month':
                trackers = TrackerModel.objects.filter(distributor_center__in=cds,
                                                       created_at__month=date.today().month)
            elif request.query_params.get('date_range') == 'this_year':
                trackers = TrackerModel.objects.filter(distributor_center__in=cds,
                                                       created_at__year=date.today().year)

            for cd in cds:
                cd_name = cd.name
                if hasattr(cd,'location_distributor_center') and cd.location_distributor_center is not None:
                     cd_name = cd.location_distributor_center.code + " - " + cd.name
                tat = trackers.filter(distributor_center=cd).aggregate(Avg('time_invested'))
                tat['time_invested__avg'] = tat['time_invested__avg'] if tat['time_invested__avg'] else 0
                count = trackers.filter(distributor_center=cd).count()
                resp.append({
                    'distributor_center': cd_name,
                    'total_trackers': count,
                    'edit_trackers': trackers.filter(distributor_center=cd, status='EDITED').count(),
                    'tat': tat['time_invested__avg'],
                    'edited_trackers': []
                })

                edited_trackers = trackers.filter(distributor_center=cd, status='EDITED').values('id', 'input_date',
                                                                                                 'output_date',
                                                                                                 'trailer__code',
                                                                                                 'transporter__code',
                                                                                                 'created_at')

                for tracker in edited_trackers:
                    tracker_details = TrackerDetailModel.objects.filter(tracker=tracker['id']).values(
                        'product__sap_code', 'product__name', 'quantity', 'tracker_product_detail__expiration_date', 'tracker_product_detail__quantity')
                    products = {}

                    for detail in tracker_details:
                        sap_code = detail['product__sap_code']
                        if sap_code not in products:
                            period = PeriodModel.objects.filter(distributor_center=cd, product__sap_code=sap_code).values('label').last()
                            products[sap_code] = {
                                'sap_code': sap_code,
                                'name': detail['product__name'],
                                'quantity': detail['quantity'],
                                'period': period['label'] if period else None,
                                'expiration_dates': [{'expiration_date': detail['tracker_product_detail__expiration_date'],
                                                     'quantity': detail['tracker_product_detail__quantity']}]
                            }
                        else:
                            products[sap_code]['expiration_dates'].append(
                                {'expiration_date': detail['tracker_product_detail__expiration_date'],
                                 'quantity': detail['tracker_product_detail__quantity']})

                    tracker['products'] = list(products.values())
                    resp[-1]['edited_trackers'].append(tracker)

        return Response(resp)
