"""
ViewSet para ExternalPerson (personas externas/proveedores)
"""
from django.db import models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ExternalPerson
from ..serializers.external_person_serializers import (
    ExternalPersonSerializer,
    ExternalPersonListSerializer,
    ExternalPersonCreateSerializer,
)


class ExternalPersonViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de personas externas (proveedores).

    Endpoints:
    - GET /api/tokens/external-persons/ - Listar
    - POST /api/tokens/external-persons/ - Crear
    - GET /api/tokens/external-persons/{id}/ - Detalle
    - PUT /api/tokens/external-persons/{id}/ - Actualizar
    - PATCH /api/tokens/external-persons/{id}/ - Actualización parcial
    - DELETE /api/tokens/external-persons/{id}/ - Eliminar (soft delete)
    - GET /api/tokens/external-persons/search/ - Búsqueda por nombre/empresa
    """
    queryset = ExternalPerson.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'company', 'identification']
    ordering_fields = ['name', 'company', 'created_at']
    ordering = ['name']
    filterset_fields = ['is_active']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExternalPersonListSerializer
        if self.action == 'create':
            return ExternalPersonCreateSerializer
        return ExternalPersonSerializer

    def get_queryset(self):
        """Solo mostrar personas activas por defecto"""
        qs = super().get_queryset()
        # Si no se especifica is_active, mostrar solo activos
        if 'is_active' not in self.request.query_params:
            qs = qs.filter(is_active=True)
        return qs

    def destroy(self, request, *args, **kwargs):
        """Soft delete: marcar como inactivo en lugar de eliminar"""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Búsqueda rápida de personas externas.
        GET /api/tokens/external-persons/search/?q=nombre
        """
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])

        qs = ExternalPerson.objects.filter(
            is_active=True
        ).filter(
            models.Q(name__icontains=query) |
            models.Q(company__icontains=query) |
            models.Q(identification__icontains=query)
        )[:20]

        serializer = ExternalPersonListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Listar solo personas externas activas.
        GET /api/tokens/external-persons/active/
        """
        qs = ExternalPerson.objects.filter(is_active=True).order_by('name')
        serializer = ExternalPersonListSerializer(qs, many=True)
        return Response(serializer.data)
