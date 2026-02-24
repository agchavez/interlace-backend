"""
Vistas para certificaciones
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Q, Count
from datetime import date, timedelta

from ..models.certification import Certification, CertificationType
from ..models.personnel import PersonnelProfile
from ..serializers.certification_serializers import (
    CertificationSerializer,
    CertificationListSerializer,
    CertificationTypeSerializer
)
from ..filters import CertificationFilter
from ..permissions import IsSupervisorOrAbove


class CertificationTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para tipos de certificación (CRUD)
    Permite crear, leer, actualizar y eliminar tipos de certificación
    """
    queryset = CertificationType.objects.all()
    serializer_class = CertificationTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Permitir filtrar por is_active"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def perform_destroy(self, instance):
        """Soft delete - solo marca como inactivo"""
        instance.is_active = False
        instance.save()


class CertificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para certificaciones del personal
    """
    queryset = Certification.objects.select_related(
        'personnel',
        'certification_type',
        'created_by'
    )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CertificationFilter
    ordering_fields = ['issue_date', 'expiration_date', 'created_at']
    ordering = ['-expiration_date']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CertificationListSerializer
        return CertificationSerializer

    def get_queryset(self):
        """Filtrar según permisos"""
        queryset = super().get_queryset()
        user = self.request.user

        # Superusuarios y staff pueden ver todas las certificaciones
        if user.is_superuser or user.is_staff:
            return queryset

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

        # Operativo solo ve sus certificaciones
        return queryset.filter(personnel=user_personnel)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Certificaciones que vencen pronto
        GET /api/personnel/certifications/expiring_soon/

        Query params:
        - days: número de días (default: 30)
        """
        days = int(request.query_params.get('days', 30))
        threshold = date.today() + timedelta(days=days)

        queryset = self.get_queryset().filter(
            expiration_date__lte=threshold,
            expiration_date__gte=date.today(),
            is_valid=True
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """
        Certificaciones vencidas
        GET /api/personnel/certifications/expired/
        """
        queryset = self.get_queryset().filter(
            expiration_date__lt=date.today(),
            is_valid=True
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revocar una certificación
        POST /api/personnel/certifications/{id}/revoke/

        Body:
        {
            "reason": "motivo de la revocación"
        }
        """
        certification = self.get_object()
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'detail': 'Debe proporcionar un motivo de revocación'},
                status=status.HTTP_400_BAD_REQUEST
            )

        certification.revoked = True
        certification.is_valid = False
        certification.revocation_reason = reason
        certification.revocation_date = date.today()
        certification.save()

        serializer = self.get_serializer(certification)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estadísticas de certificaciones
        GET /api/personnel/certifications/statistics/
        """
        queryset = self.get_queryset()

        # Por tipo
        by_type = queryset.filter(is_valid=True).values(
            'certification_type__name'
        ).annotate(
            count=Count('id')
        )

        # Por estado
        valid = queryset.filter(is_valid=True).count()
        expired = queryset.filter(
            expiration_date__lt=date.today(),
            is_valid=True
        ).count()
        expiring_30 = queryset.filter(
            expiration_date__lte=date.today() + timedelta(days=30),
            expiration_date__gte=date.today(),
            is_valid=True
        ).count()
        revoked = queryset.filter(revoked=True).count()

        data = {
            'by_type': list(by_type),
            'by_status': {
                'valid': valid,
                'expired': expired,
                'expiring_30_days': expiring_30,
                'revoked': revoked
            },
            'total': queryset.count()
        }

        return Response(data)
