# reclamos/views.py

from rest_framework import mixins, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.imported.model.claim import ClaimModel
from apps.imported.serializers.claim import ClaimSerializer
from apps.imported.utils.claim import create_reclamo, change_reclamo_state


class ClaimViewSet(
    mixins.ListModelMixin,  # GET /reclamos/
    mixins.CreateModelMixin,  # POST /reclamos/
    mixins.RetrieveModelMixin,  # GET /reclamos/<pk>/
    mixins.UpdateModelMixin,  # PUT/PATCH /reclamos/<pk>/
    mixins.DestroyModelMixin,  # DELETE /reclamos/<pk>/
    viewsets.GenericViewSet
):
    """
    ViewSet basado en mixins para manejar Reclamos.
    - Lista, crea, detalle, actualiza, elimina
    - Acción personalizada para cambiar estado
    """
    queryset = ClaimModel.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Si usas filtros:
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_class = ReclamoFilter  # Descomenta si defines un FilterSet
    search_fields = ["tipo", "descripcion"]  # Ajusta según campos
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
        """
        Aquí podrías integrar tu lógica de permisos custom.
        Por ahora, dejamos 'permissions.IsAuthenticated'.
        Si quisieras usar un CustomAccessPermission, podrías hacer:

        if self.request:
            required_perms = self.get_required_permissions(self.request.method)
            ...
        """
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Sobrescribimos create() para usar la función create_reclamo(),
        que maneja la lógica de adjuntar documentos y notificar.

        Espera multipart/form-data con:
        - tracker_id
        - assigned_user_id (opcional)
        - tipo
        - descripcion
        - doc_trailer, doc_descarga, doc_contenido, doc_producto (archivos opcionales)
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

        # Llamamos la función utilitaria
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
        Acción personalizada para cambiar el estado de un Reclamo.
        POST /reclamos/<pk>/change-state/
        Body JSON: { "new_state": "EN_PROCESO", "changed_by_id": 123 }
        """
        new_state = request.data.get("new_state")
        changed_by_id = request.data.get("changed_by_id")

        if not new_state:
            return Response({"detail": "Falta 'new_state' en el body"}, status=400)

        try:
            reclamo = change_reclamo_state(
                reclamo_id=int(pk),
                new_state=new_state,
                changed_by_id=int(changed_by_id) if changed_by_id else None
            )
        except ClaimModel.DoesNotExist:
            return Response({"detail": "Reclamo no encontrado"}, status=404)

        serializer = self.get_serializer(reclamo)
        return Response(serializer.data, status=status.HTTP_200_OK)
