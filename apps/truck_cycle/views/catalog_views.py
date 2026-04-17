"""
ViewSets para catálogos del ciclo del camión
"""
from rest_framework import viewsets, permissions
from apps.truck_cycle.models.catalogs import (
    TruckModel,
    ProductCatalogModel,
    BayModel,
    KPITargetModel,
)
from apps.truck_cycle.serializers.catalog_serializers import (
    TruckSerializer,
    ProductCatalogSerializer,
    BaySerializer,
    KPITargetSerializer,
)


def get_user_distributor_center(request):
    """Obtener el centro de distribución seleccionado por el usuario"""
    try:
        # Primero usar el CD seleccionado en el perfil de usuario
        if request.user.centro_distribucion_id:
            return request.user.centro_distribucion
        # Fallback al CD primario del perfil de personal
        return request.user.personnel_profile.primary_distributor_center
    except Exception:
        return None


class TruckViewSet(viewsets.ModelViewSet):
    """CRUD de camiones"""
    serializer_class = TruckSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return TruckModel.objects.filter(distributor_center=dc)
        return TruckModel.objects.none()

    def perform_create(self, serializer):
        dc = get_user_distributor_center(self.request)
        if dc:
            serializer.save(distributor_center=dc)


class ProductCatalogViewSet(viewsets.ModelViewSet):
    """CRUD de catálogo de productos"""
    serializer_class = ProductCatalogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return ProductCatalogModel.objects.filter(distributor_center=dc)
        return ProductCatalogModel.objects.none()

    def perform_create(self, serializer):
        dc = get_user_distributor_center(self.request)
        if dc:
            serializer.save(distributor_center=dc)


class BayViewSet(viewsets.ModelViewSet):
    """CRUD de andenes"""
    serializer_class = BaySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return BayModel.objects.filter(distributor_center=dc)
        return BayModel.objects.none()

    def perform_create(self, serializer):
        dc = get_user_distributor_center(self.request)
        if dc:
            serializer.save(distributor_center=dc)


class KPITargetViewSet(viewsets.ModelViewSet):
    """CRUD de metas de KPI"""
    serializer_class = KPITargetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dc = get_user_distributor_center(self.request)
        if dc:
            return KPITargetModel.objects.filter(distributor_center=dc)
        return KPITargetModel.objects.none()

    def perform_create(self, serializer):
        dc = get_user_distributor_center(self.request)
        if dc:
            serializer.save(distributor_center=dc)
