"""
Vistas para métricas de desempeño
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Q, Avg, Sum, Count
from datetime import date, timedelta

from ..models.performance import PerformanceMetric
from ..models.personnel import PersonnelProfile
from ..serializers.performance_serializers import (
    PerformanceMetricSerializer,
    PerformanceMetricListSerializer
)
from ..filters import PerformanceMetricFilter
from ..permissions import IsSupervisorOrAbove


class PerformanceMetricViewSet(viewsets.ModelViewSet):
    """
    ViewSet para métricas de desempeño

    Solo supervisores y superiores pueden crear/editar
    """
    queryset = PerformanceMetric.objects.select_related(
        'personnel',
        'evaluated_by'
    )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PerformanceMetricFilter
    ordering_fields = ['metric_date', 'productivity_rate', 'supervisor_rating']
    ordering = ['-metric_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return PerformanceMetricListSerializer
        return PerformanceMetricSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisorOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filtrar según permisos"""
        queryset = super().get_queryset()
        user = self.request.user

        try:
            user_personnel = user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return queryset.none()

        # Gerente CD ve todo su centro
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return queryset.filter(
                personnel__primary_distributor_center=user_personnel.primary_distributor_center
            )

        # Jefe de área ve su área
        if user_personnel.hierarchy_level == PersonnelProfile.AREA_MANAGER:
            return queryset.filter(personnel__area=user_personnel.area)

        # Supervisor ve su equipo
        if user_personnel.hierarchy_level == PersonnelProfile.SUPERVISOR:
            subordinates_ids = [p.id for p in user_personnel.get_all_subordinates()]
            return queryset.filter(
                Q(personnel=user_personnel) |
                Q(personnel__id__in=subordinates_ids)
            )

        # Operativo solo ve sus métricas
        return queryset.filter(personnel=user_personnel)

    @action(detail=False, methods=['get'])
    def team_performance(self, request):
        """
        Desempeño del equipo
        GET /api/personnel/performance/team_performance/

        Query params:
        - period: DAILY|WEEKLY|MONTHLY
        - days: número de días atrás (default: 30)
        """
        period = request.query_params.get('period', 'DAILY')
        days = int(request.query_params.get('days', 30))
        start_date = date.today() - timedelta(days=days)

        queryset = self.get_queryset().filter(
            period=period,
            metric_date__gte=start_date
        )

        stats = queryset.aggregate(
            avg_productivity=Avg('productivity_rate'),
            avg_rating=Avg('supervisor_rating'),
            total_pallets=Sum('pallets_moved'),
            total_hours=Sum('hours_worked'),
            total_errors=Sum('errors_count'),
            total_accidents=Sum('accidents_count')
        )

        # Por persona
        by_person = queryset.values(
            'personnel__employee_code',
            'personnel__first_name',
            'personnel__last_name'
        ).annotate(
            avg_productivity=Avg('productivity_rate'),
            avg_rating=Avg('supervisor_rating'),
            total_pallets=Sum('pallets_moved')
        )

        data = {
            'period': period,
            'date_range': {
                'from': start_date,
                'to': date.today()
            },
            'team_stats': stats,
            'by_person': list(by_person)
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """
        Mejores desempeños
        GET /api/personnel/performance/top_performers/

        Query params:
        - period: DAILY|WEEKLY|MONTHLY
        - limit: número de resultados (default: 10)
        - days: número de días atrás (default: 30)
        """
        period = request.query_params.get('period', 'MONTHLY')
        limit = int(request.query_params.get('limit', 10))
        days = int(request.query_params.get('days', 30))
        start_date = date.today() - timedelta(days=days)

        # Calcular promedio por persona
        top_performers = self.get_queryset().filter(
            period=period,
            metric_date__gte=start_date
        ).values(
            'personnel__id',
            'personnel__employee_code',
            'personnel__first_name',
            'personnel__last_name',
            'personnel__position'
        ).annotate(
            avg_productivity=Avg('productivity_rate'),
            avg_rating=Avg('supervisor_rating'),
            total_pallets=Sum('pallets_moved'),
            error_rate=Avg('errors_count')
        ).order_by('-avg_productivity')[:limit]

        return Response(list(top_performers))
