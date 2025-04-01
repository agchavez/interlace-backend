from rest_framework import mixins, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.imported.model.claim import ClaimModel
from apps.imported.serializers.claim import ClaimSerializer
from apps.imported.utils.claim import create_reclamo, change_reclamo_state
from apps.imported.utils.validation_claim import validate_create_claim
from django_filters import rest_framework as django_filters
from django.db.models import Q
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from django.http import FileResponse
import io

class ClaimFilter(django_filters.FilterSet):
    tipo = django_filters.CharFilter(
        field_name='claim_type',
        lookup_expr='exact'
    )
    class Meta:
        model = ClaimModel
        fields = {
            'id': ['exact'],
            'status': ['exact'],
        }

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
    filterset_class = ClaimFilter
    # filterset_class = ReclamoFilter  # Descomenta si defines un FilterSet
    search_fields = ["claim_type", "status", "tracker__distributor_center__name"]
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
        filters = {}
        if request.query_params.get('status'):
            filters['status'] = request.query_params.get('status')
        if request.query_params.get('tipo'):
            filters['claim_type'] = request.query_params.get('tipo')
        if request.query_params.get('distributor_center'):
            filters['tracker__distributor_center__id'] = request.query_params.get('distributor_center')
        if request.query_params.get('date_after'):
            filters['created_at__gte'] = request.query_params.get('date_after')
        if request.query_params.get('date_before'):
            filters['created_at__lte'] = request.query_params.get('date_before')
        queryset = queryset.filter(**filters)
        
        if request.query_params.get('search'):
            search = request.query_params.get('search')
            queryset = queryset.filter(
                Q(claim_type__icontains=search) | 
                Q(description__icontains=search) |
                Q(tracker__distributor_center__name__icontains=search)
            )

        # limit y offset para paginación
        limit = int(self.request.query_params.get('limit', 10))
        offset = int(self.request.query_params.get('offset', 0))
        count = queryset.count()
        queryset = queryset[offset:offset+limit]
        serializer = self.get_serializer(queryset, many=True)
        # Resultados paginados
        body = {
            "count": count,
            "results": serializer.data
        }
        return Response(body, status=status.HTTP_200_OK)
    

    @action(methods=["get"], detail=True, url_path="download-file")
    def download_file(self, request, pk=None):
        """
        Descarga un archivo de la reclamación
        """
        reclamo = self.get_object()
        if reclamo is None:
            return Response({"detail": "No se encontró el archivo"}, status=status.HTTP_404_NOT_FOUND)
        # validar el nombre del archivo
        valido = False
        filename = request.GET.get('filename')
        if reclamo.claim_file is not None and reclamo.claim_file == filename:
            valido = True
        elif reclamo.credit_memo_file is not None and reclamo.credit_memo_file == filename:
            valido = True
        elif reclamo.observations_file is not None and reclamo.observations_file == filename:
            valido = True
        
        for photo in reclamo.photos_container_closed.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_container_one_open.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_container_two_open.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_container_top.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_during_unload.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_pallet_damage.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_damaged_product_base.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_damaged_product_dents.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_damaged_boxes.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_grouped_bad_product.all():
            if photo.file == filename:
                valido = True
                break
        for photo in reclamo.photos_repalletized.all():
            if photo.file == filename:
                valido = True
                break
        
        if not valido:
            return Response({"detail": "No se encontró el archivo"}, status=status.HTTP_404_NOT_FOUND)
        
        blob_service_client = BlobServiceClient(account_url=f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net", credential=settings.AZURE_ACCOUNT_KEY)
        blob_client = blob_service_client.get_blob_client(container=settings.AZURE_CONTAINER, blob=filename)
        blob_data = blob_client.download_blob().readall()
        return FileResponse(io.BytesIO(blob_data), as_attachment=True, filename=filename)
