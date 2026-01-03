"""
Vistas para registros médicos
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Q, Count
from datetime import date

from ..models.medical import MedicalRecord
from ..models.personnel import PersonnelProfile
from ..serializers.medical_serializers import (
    MedicalRecordSerializer,
    MedicalRecordListSerializer
)
from ..filters import MedicalRecordFilter
from ..permissions import CanViewMedicalRecords


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registros médicos

    NOTA: Los registros médicos son confidenciales
    Solo accesible por:
    - El propio empleado
    - Área de People/RRHH
    - Gerente de CD (mismo centro)
    """
    queryset = MedicalRecord.objects.select_related(
        'personnel',
        'created_by'
    )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MedicalRecordFilter
    ordering_fields = ['record_date', 'created_at']
    ordering = ['-record_date']
    permission_classes = [IsAuthenticated, CanViewMedicalRecords]

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicalRecordListSerializer
        return MedicalRecordSerializer

    def get_queryset(self):
        """Filtrar según permisos"""
        queryset = super().get_queryset()
        user = self.request.user

        try:
            user_personnel = user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return queryset.none()

        # Área de People ve todo
        if user_personnel.area.code == 'PEOPLE':
            return queryset

        # Gerente CD ve su centro
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return queryset.filter(
                personnel__primary_distributor_center=user_personnel.primary_distributor_center
            )

        # Solo propios registros
        return queryset.filter(personnel=user_personnel)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active_incapacities(self, request):
        """
        Listar incapacidades activas
        GET /api/personnel/medical-records/active_incapacities/
        """
        queryset = self.get_queryset().filter(
            record_type=MedicalRecord.INCAPACITY,
            end_date__gte=date.today()
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def followup_required(self, request):
        """
        Registros que requieren seguimiento
        GET /api/personnel/medical-records/followup_required/
        """
        queryset = self.get_queryset().filter(
            requires_followup=True,
            followup_date__gte=date.today()
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estadísticas de registros médicos
        GET /api/personnel/medical-records/statistics/
        """
        queryset = self.get_queryset()

        by_type = queryset.values('record_type').annotate(
            count=Count('id')
        )

        active_incapacities = queryset.filter(
            record_type=MedicalRecord.INCAPACITY,
            end_date__gte=date.today()
        ).count()

        data = {
            'by_type': list(by_type),
            'active_incapacities': active_incapacities,
            'total_records': queryset.count()
        }

        return Response(data)
