"""
ViewSets para modelos operativos del ciclo del camión
"""
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from apps.truck_cycle.models.operational import (
    InconsistencyModel,
    PautaPhotoModel,
    PalletTicketModel,
)
from apps.truck_cycle.serializers.operational_serializers import (
    InconsistencySerializer,
    PautaPhotoSerializer,
    PalletTicketSerializer,
)


def get_user_distributor_center(request):
    """Obtener el centro de distribución del usuario actual"""
    try:
        return request.user.personnelprofile.primary_distributor_center
    except Exception:
        return None


class InconsistencyViewSet(viewsets.ModelViewSet):
    """Gestión de inconsistencias"""
    serializer_class = InconsistencySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return InconsistencyModel.objects.filter(
                pauta__distributor_center=dc
            )
        return InconsistencyModel.objects.none()

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class PautaPhotoViewSet(viewsets.ModelViewSet):
    """Gestión de fotos de pautas"""
    serializer_class = PautaPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return PautaPhotoModel.objects.filter(
                pauta__distributor_center=dc
            )
        return PautaPhotoModel.objects.none()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class PalletTicketViewSet(viewsets.ModelViewSet):
    """Gestión de tickets de tarima"""
    serializer_class = PalletTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return PalletTicketModel.objects.filter(
                pauta__distributor_center=dc
            )
        return PalletTicketModel.objects.none()
