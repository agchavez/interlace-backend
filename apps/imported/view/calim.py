from rest_framework import mixins, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.document.utils.documents import create_documento
from apps.imported.model.claim import ClaimModel
from apps.imported.serializers.claim import ClaimSerializer
from apps.imported.utils.claim import create_reclamo, change_reclamo_state
from apps.imported.utils.validation_claim import validate_create_claim


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
         - claimNumber, discardDoc, observations
         - y en request.FILES: diversos archivos de fotos y documentos
        """
        tracker_id = request.data.get("tracker_id")

        # Validamos los datos del request usando nuestra nueva utilidad
        user, tracker, _ = validate_create_claim(request, tracker_id=tracker_id)

        # Extraemos los datos del request
        assigned_user_id = request.data.get("assigned_user_id")
        claim_type = request.data.get("claim_type")
        descripcion = request.data.get("descripcion")

        # Campos adicionales
        claim_number = request.data.get("claim_number")
        discard_doc = request.data.get("discard_doc")
        observations = request.data.get("observations")

        # Archivos de documentos
        claim_file = request.FILES.get("claim_file")
        credit_memo_file = request.FILES.get("credit_memo_file")
        observations_file = request.FILES.get("observations_file")

        # Fotografías por categoría
        photo_files = {}
        photo_categories = [
            "photos_container_closed", "photos_container_one_open",
            "photos_container_two_open", "photos_container_top",
            "photos_during_unload", "photos_pallet_damage",
            "photos_damaged_product_base", "photos_damaged_product_dents",
            "photos_damaged_boxes", "photos_grouped_bad_product",
            "photos_repalletized"
        ]

        for category in photo_categories:
            if category in request.FILES:
                photo_files[category] = request.FILES.getlist(category)

        # Llamamos la función utilitaria para crear el claim
        reclamo = create_reclamo(
            tracker_id=int(tracker_id),
            assigned_user_id=int(assigned_user_id) if assigned_user_id else None,
            claim_type=claim_type,
            description=descripcion,
            claim_number=claim_number,
            discard_doc=discard_doc,
            observations=observations,
            claim_file=claim_file,
            credit_memo_file=credit_memo_file,
            observations_file=observations_file,
            photo_files=photo_files
        )

        serializer = self.get_serializer(reclamo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True, url_path="upload-photos")
    def upload_photos(self, request, pk=None):
        """
        API para cargar fotos adicionales o sustituir existentes en un claim.

        Parámetros esperados:
        - photo_category: Categoría de foto (requerido)
        - mode: "add" (agregar) o "replace" (sustituir), por defecto "add"
        - FILES: Los archivos a cargar

        Ejemplos de categorías:
        - photos_container_closed
        - photos_damaged_boxes
        - etc.
        """
        try:
            claim = self.get_object()
        except ClaimModel.DoesNotExist:
            return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Obtener categoría de fotos
        photo_category = request.data.get("photo_category")
        if not photo_category:
            return Response(
                {"detail": "Falta el parámetro 'photo_category'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar categoría
        valid_categories = [
            "photos_container_closed", "photos_container_one_open",
            "photos_container_two_open", "photos_container_top",
            "photos_during_unload", "photos_pallet_damage",
            "photos_damaged_product_base", "photos_damaged_product_dents",
            "photos_damaged_boxes", "photos_grouped_bad_product",
            "photos_repalletized"
        ]

        if photo_category not in valid_categories:
            return Response(
                {"detail": f"Categoría de foto inválida. Opciones válidas: {', '.join(valid_categories)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Modo: add (agregar) o replace (sustituir)
        mode = request.data.get("mode", "add")
        if mode not in ["add", "replace"]:
            return Response(
                {"detail": "El parámetro 'mode' debe ser 'add' o 'replace'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener archivos
        files = request.FILES.getlist("files")
        if not files:
            return Response(
                {"detail": "No se encontraron archivos para subir"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mapeo de nombres a relaciones M2M
        photo_fields = {
            "photos_container_closed": claim.photos_container_closed,
            "photos_container_one_open": claim.photos_container_one_open,
            "photos_container_two_open": claim.photos_container_two_open,
            "photos_container_top": claim.photos_container_top,
            "photos_during_unload": claim.photos_during_unload,
            "photos_pallet_damage": claim.photos_pallet_damage,
            "photos_damaged_product_base": claim.photos_damaged_product_base,
            "photos_damaged_product_dents": claim.photos_damaged_product_dents,
            "photos_damaged_boxes": claim.photos_damaged_boxes,
            "photos_grouped_bad_product": claim.photos_grouped_bad_product,
            "photos_repalletized": claim.photos_repalletized
        }

        # Nombres descriptivos para las categorías
        field_descriptions = {
            "photos_container_closed": "Contenedor cerrado",
            "photos_container_one_open": "Contenedor con 1 puerta abierta",
            "photos_container_two_open": "Contenedor con 2 puertas abiertas",
            "photos_container_top": "Vista superior del contenido",
            "photos_during_unload": "Durante la descarga",
            "photos_pallet_damage": "Fisuras/abolladuras de pallets",
            "photos_damaged_product_base": "Base de producto dañada",
            "photos_damaged_product_dents": "Abolladuras del producto",
            "photos_damaged_boxes": "Cajas dañadas",
            "photos_grouped_bad_product": "Producto en mal estado agrupado",
            "photos_repalletized": "Repaletizado de producto dañado"
        }

        # Si es modo "replace", eliminar fotos existentes
        if mode == "replace":
            photo_fields[photo_category].clear()

        # Obtener el número de fotos actuales para la categoría
        current_count = photo_fields[photo_category].count()

        # Agregar fotos nuevas
        desc = field_descriptions.get(photo_category, photo_category)
        uploaded_docs = []

        for i, file_obj in enumerate(files):
            doc = create_documento(
                file_obj,
                name=f"{desc} #{current_count + i + 1}",
                folder="Claim",
                subfolder=claim.claim_code
            )
            photo_fields[photo_category].add(doc)
            uploaded_docs.append(doc)

        return Response({
            "detail": f"{len(files)} fotos {mode == 'replace' and 'reemplazadas' or 'agregadas'} correctamente",
            "count": photo_fields[photo_category].count(),
            "category": photo_category,
            "claim_id": claim.id
        }, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path="change-state")
    def change_state(self, request, pk=None):
        """
        Cambia el estado del claim.
        Se espera en el body: { "new_state": "...", "changed_by_id": <id> , "observations": "..." }
        """
        new_state = request.data.get("new_state")
        changed_by_id = request.data.get("changed_by_id")
        observations = request.data.get("observations")

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