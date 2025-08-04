from click.core import F
from django.db.models import Avg
from rest_framework import viewsets
from datetime import date, timedelta
from rest_framework import serializers
from rest_framework.response import Response

from apps.maintenance.exceptions.maintenance import DistributionCenterDoesNotExistError, NoDistributionCenterError
from apps.tracker.models.tracker import TrackerModel
from apps.user.views.user import CustomAccessPermission
from apps.maintenance.models.distributor_center import DistributorCenter
# Grafica de TAT(tiempo promedio de entrega) por mes, centro de distribucion y año
class TATSerializer(serializers.Serializer):
    # lista de años disponibles (2023 en adelante)
    year = serializers.ListField(child=serializers.IntegerField(), required=False)
    # centros de distribucion, solo si el usuario no tiene asignado un centro de distribucion
    distributor_center = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate(self, attrs):
        # si no se envia el año se toma el año actual
        if not attrs.get('year'):
            attrs['year'] = [date.today().year]
        # validar que los años sean validos
        for year in attrs.get('year'):
            if year < date.today().year:
                raise serializers.ValidationError('El año no puede ser menor al año actual')
        # si el usuario no tiene un centro de distribucion asignado se debe enviar los centros de distribucion
        if self.context['request'].user.distributions_centers.exists():
            if not attrs.get('distributor_center'):
                raise NoDistributionCenterError()
            else:
                # validar que los centros de distribucion existan
                for distributor_center in attrs.get('distributor_center'):
                    if not DistributorCenter.objects.filter(id=distributor_center).exists():
                        raise DistributionCenterDoesNotExistError
        return attrs


class TATAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = TATSerializer
    permission_classes = [CustomAccessPermission]

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
        if request.user.distributions_centers.exists():
            distributor_center = request.query_params.get('distributor_center')
            if distributor_center:
                distributor_center = [int(x) for x in distributor_center.split(',')]
            else:
                distributor_center = []
        else:
            distributor_center = [request.user.centro_distribucion.id]
        year = request.query_params.get('year')
        if year:
            year = [int(x) for x in year.split(',')]
        else:
            year = [date.today().year]

        if not distributor_center:
            return Response([])

        try:
            filtered_qs = TrackerModel.objects.filter(
                created_at__year__in=year,
                distributor_center_id__in=distributor_center,
                status='COMPLETE',
                exclude_tat=False
            )

            queryset = (filtered_qs
                        .values('created_at__month', 'created_at__year', 'distributor_center_id')
                        .annotate(avg_time_invested=Avg('time_invested'))
                        .order_by('created_at__month', 'created_at__year', 'distributor_center_id')
                        )
            queryset_list = list(queryset)
        except Exception as e:
            import logging
            logging.error(f"Error en queryset TATAPI: {e}")
            return Response({'error': str(e)}, status=500)

        months = [x for x in range(1, 13)]
        years = year
        distributor_centers = DistributorCenter.objects.filter(id__in=distributor_center)
        data = []

        for month in months:
            for year_item in years:
                for dc in distributor_centers:
                    avg_time_invested = 0
                    for q in queryset_list:
                        if (q['created_at__month'] == month and
                            q['created_at__year'] == year_item and
                            q['distributor_center_id'] == dc.id):
                            avg = q.get('avg_time_invested', 0)
                            avg_time_invested = (avg / 60) if avg else 0
                            break

                    data.append({
                        'month': month,
                        'year': year_item,
                        'distributor_center': dc.id,
                        'distributor_center_name': dc.name,
                        'avg_time_invested': avg_time_invested
                    })
        return Response(data)
