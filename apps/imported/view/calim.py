from rest_framework import mixins, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.imported.model.claim import ClaimModel
from apps.imported.serializers.claim import ClaimSerializer
from apps.imported.utils.claim import create_reclamo, change_reclamo_state


class ClaimViewSet(
    mixins.ListModelMixin,      # GET /claims/
    mixins.CreateModelMixin,    # POST /claims/
    mixins.RetrieveModelMixin,  # GET /claims/<pk>/
    mixins.UpdateModelMixin,    # PUT/PATCH /claims/<pk>/
    mixins.DestroyModelMixin,   # DELETE /claims/<pk>/
    viewsets.GenericViewSet
):
    """
    ViewSet para manejar Claims:
     - Listado, creación, detalle, actualización y eliminación.
     - Acción personalizada para cambiar estado.
    """
    queryset = ClaimModel.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = []  # Agrega tus permisos según convenga

    # Configuración de filtros y ordenación
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_class = ReclamoFilter  # Descomenta si defines un FilterSet
    search_fields = ["tipo", "descripcion"]
    ordering_fields = ["created_at", "tipo", "status"]

    PERMISSION_MAPPING = {
        "GET": ["claims.view_reclamomodel"],
        "POST": ["claims.add_reclamomodel"],
        "PUT": ["claims.change_reclamomodel"],
        "PATCH": ["claims.change_reclamomodel"],
        "DELETE": ["claims.delete_reclamomodel"],
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    def get_permissions(self):
        # Aquí podrías integrar tu CustomAccessPermission si lo deseas.
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Espera en request.data:
         - tracker_id, assigned_user_id, tipo, descripcion
         - y en request.FILES: doc_trailer, doc_descarga, doc_contenido, doc_producto
        """
        tracker_id = request.data.get("tracker_id")
        assigned_user_id = request.data.get("assigned_user_id")
        tipo = request.data.get("tipo")
        descripcion = request.data.get("descripcion")

        doc_trailer_file = request.FILES.get("doc_trailer")
        doc_descarga_file = request.FILES.get("doc_descarga")
        doc_contenido_file = request.FILES.get("doc_contenido")
        doc_producto_file = request.FILES.get("doc_producto")

        if not tracker_id or not tipo or not descripcion:
            return Response(
                {"detail": "Faltan datos obligatorios (tracker_id, tipo, descripcion)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Llamamos la función utilitaria para crear el claim
        reclamo = create_reclamo(
            tracker_id=int(tracker_id),
            assigned_user_id=int(assigned_user_id) if assigned_user_id else None,
            tipo=tipo,
            descripcion=descripcion,
            doc_trailer_file=doc_trailer_file,
            doc_descarga_file=doc_descarga_file,
            doc_contenido_file=doc_contenido_file,
            doc_producto_file=doc_producto_file,
        )

        serializer = self.get_serializer(reclamo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True, url_path="change-state")
    def change_state(self, request, pk=None):
        """
        Cambia el estado del claim.
        Se espera en el body: { "new_state": "...", "changed_by_id": <id> }
        """
        new_state = request.data.get("new_state")
        changed_by_id = request.data.get("changed_by_id")

        if not new_state:
            return Response({"detail": "Falta 'new_state' en el body"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reclamo = change_reclamo_state(
                reclamo_id=int(pk),
                new_state=new_state,
                changed_by_id=int(changed_by_id) if changed_by_id else None
            )
        except ClaimModel.DoesNotExist:
            return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(reclamo)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="mis-claims")
    def mis_claims(self, request):
        """
        Devuelve los reclamos asociados a los centros de distribución a los que tiene acceso el usuario.
        Se obtienen tanto del campo 'centro_distribucion' como de la relación 'distributions_centers'.
        """
        user = request.user
        dc_ids = []
        # Si el usuario tiene asignado un centro de distribución principal
        if hasattr(user, "centro_distribucion") and user.centro_distribucion:
            dc_ids.append(user.centro_distribucion.id)
        # Agregar los centros a los que el usuario tiene acceso (many-to-many)
        if hasattr(user, "distributions_centers"):
            dc_ids += list(user.distributions_centers.values_list("id", flat=True))
        # Filtrar reclamos cuyo tracker tenga uno de esos centros
        queryset = self.get_queryset().filter(tracker__distributor_center__id__in=dc_ids)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)