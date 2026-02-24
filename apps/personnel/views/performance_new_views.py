"""
Vistas para el nuevo sistema de evaluaciones con métricas escalables
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Q, Avg, Count
from datetime import date, timedelta

from ..models.performance_new import (
    PerformanceMetricType,
    PerformanceEvaluation,
    EvaluationMetricValue
)
from ..models.personnel import PersonnelProfile
from ..serializers.performance_new_serializers import (
    PerformanceMetricTypeSerializer,
    PerformanceMetricTypeListSerializer,
    PerformanceEvaluationSerializer,
    PerformanceEvaluationListSerializer,
    PerformanceEvaluationCreateSerializer,
    EvaluationMetricValueSerializer
)
from ..permissions import IsSupervisorOrAbove, CanManagePersonnel


class PerformanceMetricTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para tipos de métricas de desempeño

    Permite configurar métricas personalizadas que se asignan a tipos de posición
    """
    queryset = PerformanceMetricType.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['display_order', 'name']
    filterset_fields = {
        'is_active': ['exact'],
        'metric_type': ['exact', 'in'],
        'is_required': ['exact'],
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return PerformanceMetricTypeListSerializer
        return PerformanceMetricTypeSerializer

    def get_permissions(self):
        """Solo gestores de personal pueden crear/editar/eliminar"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManagePersonnel()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Asignar usuario creador"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def for_position_type(self, request):
        """
        Obtiene las métricas aplicables para un tipo de posición

        Query params:
        - position_type: Tipo de posición (PICKER, COUNTER, etc.)
        """
        position_type = request.query_params.get('position_type')

        if not position_type:
            return Response(
                {'error': 'position_type es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener métricas activas que aplican para esta posición
        metrics = PerformanceMetricType.objects.filter(
            is_active=True
        ).filter(
            Q(applicable_position_types__contains=[position_type]) |
            Q(applicable_position_types=[]) |
            Q(applicable_position_types__isnull=True)
        ).order_by('display_order', 'name')

        serializer = PerformanceMetricTypeSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reordenar métricas

        Body: [{"id": 1, "display_order": 0}, {"id": 2, "display_order": 1}, ...]
        """
        if not request.user.has_perm('personnel.manage_personnel'):
            return Response(
                {'error': 'No tiene permisos para reordenar métricas'},
                status=status.HTTP_403_FORBIDDEN
            )

        order_data = request.data
        if not isinstance(order_data, list):
            return Response(
                {'error': 'Se espera una lista de objetos {id, display_order}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar orden
        for item in order_data:
            try:
                metric = PerformanceMetricType.objects.get(id=item['id'])
                metric.display_order = item['display_order']
                metric.save()
            except (PerformanceMetricType.DoesNotExist, KeyError):
                continue

        return Response({'status': 'success', 'message': 'Orden actualizado correctamente'})


class PerformanceEvaluationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para evaluaciones de desempeño

    Gestiona las evaluaciones con métricas dinámicas
    """
    queryset = PerformanceEvaluation.objects.select_related(
        'personnel',
        'evaluated_by'
    ).prefetch_related('metric_values__metric_type')
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['personnel__employee_code', 'personnel__first_name', 'personnel__last_name']
    ordering_fields = ['evaluation_date', 'overall_score', 'created_at']
    ordering = ['-evaluation_date']
    filterset_fields = {
        'personnel': ['exact'],
        'period': ['exact', 'in'],
        'is_draft': ['exact'],
        'evaluation_date': ['gte', 'lte', 'exact'],
        'evaluated_by': ['exact'],
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return PerformanceEvaluationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PerformanceEvaluationCreateSerializer
        return PerformanceEvaluationSerializer

    def get_permissions(self):
        """Solo supervisores y superiores pueden crear/editar"""
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

        # Operativo solo ve sus evaluaciones
        return queryset.filter(personnel=user_personnel)

    def perform_create(self, serializer):
        """Asignar evaluador si no está especificado"""
        try:
            personnel_profile = self.request.user.personnel_profile
            if not serializer.validated_data.get('evaluated_by'):
                serializer.save(evaluated_by=personnel_profile)
            else:
                serializer.save()
        except PersonnelProfile.DoesNotExist:
            serializer.save()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Finalizar evaluación (cambiar de borrador a enviada)

        Calcula el score general y marca como enviada
        """
        evaluation = self.get_object()

        if not evaluation.is_draft:
            return Response(
                {'error': 'Esta evaluación ya ha sido enviada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que todas las métricas requeridas estén completas
        position_type = evaluation.personnel.position_type
        required_metrics = PerformanceMetricType.objects.filter(
            is_active=True,
            is_required=True
        ).filter(
            Q(applicable_position_types__contains=[position_type]) |
            Q(applicable_position_types=[]) |
            Q(applicable_position_types__isnull=True)
        )

        completed_metrics = evaluation.metric_values.values_list('metric_type_id', flat=True)
        missing_metrics = required_metrics.exclude(id__in=completed_metrics)

        if missing_metrics.exists():
            missing_names = [m.name for m in missing_metrics]
            return Response(
                {
                    'error': 'Faltan métricas requeridas',
                    'missing_metrics': missing_names
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marcar como enviada
        from django.utils import timezone
        evaluation.is_draft = False
        evaluation.submitted_at = timezone.now()
        evaluation.overall_score = evaluation.calculate_overall_score()
        evaluation.save()

        serializer = self.get_serializer(evaluation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estadísticas de evaluaciones

        Query params:
        - period: WEEKLY|MONTHLY|QUARTERLY|ANNUAL
        - start_date: Fecha inicio (YYYY-MM-DD)
        - end_date: Fecha fin (YYYY-MM-DD)
        """
        queryset = self.get_queryset().filter(is_draft=False)

        # Filtros
        period = request.query_params.get('period')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if period:
            queryset = queryset.filter(period=period)

        if start_date:
            queryset = queryset.filter(evaluation_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(evaluation_date__lte=end_date)

        # Calcular estadísticas
        stats = queryset.aggregate(
            total_evaluations=Count('id'),
            avg_score=Avg('overall_score')
        )

        # Por personal
        by_personnel = queryset.values(
            'personnel__id',
            'personnel__employee_code',
            'personnel__first_name',
            'personnel__last_name',
            'personnel__position'
        ).annotate(
            evaluations_count=Count('id'),
            avg_score=Avg('overall_score')
        ).order_by('-avg_score')[:20]

        return Response({
            'statistics': stats,
            'top_performers': list(by_personnel)
        })


class EvaluationMetricValueViewSet(viewsets.ModelViewSet):
    """
    ViewSet para valores de métricas

    Permite gestionar los valores individuales de métricas en evaluaciones
    """
    queryset = EvaluationMetricValue.objects.select_related(
        'evaluation__personnel',
        'metric_type'
    )
    serializer_class = EvaluationMetricValueSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    filterset_fields = {
        'evaluation': ['exact'],
        'metric_type': ['exact'],
    }

    def get_permissions(self):
        """Solo supervisores pueden crear/editar"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisorOrAbove()]
        return [IsAuthenticated()]
