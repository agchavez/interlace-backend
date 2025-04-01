from rest_framework import mixins, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.document.utils.documents import create_documento
from apps.imported.model import ClaimProductModel
from apps.imported.model.claim import ClaimModel
from apps.imported.serializers import ClaimProductSerializer
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
        # State
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
        
        # Claim Number
        if "new_claim_number" in request.data:
            claim_number = request.data.get("new_claim_number")
            try:
                reclamo.claim_number = claim_number
                reclamo.save()
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        # Discard Doc
        if "new_discard_doc" in request.data:
            discard_doc = request.data.get("new_discard_doc")
            try:
                reclamo.discard_doc = discard_doc
                reclamo.save()
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        # Observations
        if "new_observations" in request.data:
            observations = request.data.get("new_observations")
            try:
                reclamo.observations = observations
                reclamo.save()
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Claim File
        new_claim_file = request.FILES.get("new_claim_file")
        if new_claim_file:
            # En lugar de asignar directamente, usar create_documento()
            doc_claim = create_documento(new_claim_file,new_claim_file.name,  "Claim", reclamo.claim_code)
            reclamo.claim_file = doc_claim.file

        # Claim Credit Memo File
        new_credit_memo_file = request.FILES.get("new_credit_memo_file")
        if new_credit_memo_file:
            doc_credit = create_documento(new_credit_memo_file, new_credit_memo_file.name, "Claim", reclamo.claim_code)
            reclamo.credit_memo_file = doc_credit.file

        # Claim Observations File
        new_observations_file = request.FILES.get("new_observations_file")
        if new_observations_file:
            doc_obs = create_documento(new_observations_file, new_observations_file.name, "Claim", reclamo.claim_code)
            reclamo.observations_file = doc_obs.file

        reclamo.save()
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
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="tracker/(?P<tracker_id>\d+)")
    def get_claim_by_tracker(self, request, tracker_id=None):
        """
        Devuelve los reclamos asociados a un tracker específico.
        """
        queryset = self.get_queryset().filter(tracker__id=tracker_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["patch"], detail=True, url_path="update-claim")
    def update_claim(self, request, pk=None):
        """
        Acción personalizada que recibe todo el "nuevo estado" del reclamo
        y gestiona campos principales, archivos, fotos y productos.
        """
        try:
            claim = self.get_object()  # ClaimModel con pk=pk
        except ClaimModel.DoesNotExist:
            return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        # 1. Actualizar campos principales
        claim_type = data.get("claim_type", claim.claim_type)
        description = data.get("description", claim.description)
        claim_number = data.get("claim_number", claim.claim_number)
        discard_doc = data.get("discard_doc", claim.discard_doc)
        observations = data.get("observations", claim.observations)

        claim.claim_type = claim_type
        claim.description = description
        claim.claim_number = claim_number
        claim.discard_doc = discard_doc
        claim.observations = observations

        # 2. Actualizar archivos principales (claim_file, credit_memo_file, observations_file)
        #    - Si te envían un file nuevo, lo reemplazas
        #    - Si te envían null y antes existía, decides si borrar o no
        if "claim_file" in request.FILES:
            file_obj = request.FILES["claim_file"]
            doc_claim = create_documento(file_obj, file_obj.name, "Claim", claim.claim_code)
            claim.claim_file = doc_claim.file
        elif data.get("claim_file") is None:
            # Te están indicando que ya no quieren el archivo
            claim.claim_file = None

        if "credit_memo_file" in request.FILES:
            file_obj = request.FILES["credit_memo_file"]
            doc_credit = create_documento(file_obj, file_obj.name, "Claim", claim.claim_code)
            claim.credit_memo_file = doc_credit.file
        elif data.get("credit_memo_file") is None:
            claim.credit_memo_file = None

        if "observations_file" in request.FILES:
            file_obj = request.FILES["observations_file"]
            doc_obs = create_documento(file_obj, file_obj.name, "Claim", claim.claim_code)
            claim.observations_file = doc_obs.file
        elif data.get("observations_file") is None:
            claim.observations_file = None

        claim.save()

        # 3. Actualizar fotos (M2M). Esperamos un formato como:
        #
        #   {
        #     "photos_container_closed": {
        #        "remove": [ID1, ID2],
        #        "add": [ <File1>, <File2> ]
        #     },
        #     "photos_container_one_open": { ... },
        #     ...
        #   }
        #
        # Si no recibes JSON anidado sino algo distinto, ajústalo.
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
            "photos_repalletized": claim.photos_repalletized,
        }

        for field_name, m2m_relation in photo_fields.items():
            if field_name in data:
                cat_data = data[field_name]  # { "remove": [...], "add": [...] }

                # a) Eliminar fotos
                to_remove = cat_data.get("remove", [])
                if to_remove:
                    m2m_relation.remove(*to_remove)  # Elimina esos DocumentModel IDs de la M2M
                    # Opcionalmente, podrías borrarlos definitivamente de DocumentModel.objects.get(pk=)
                    # si tu lógica lo requiere.

                # b) Agregar fotos nuevas
                if field_name in request.FILES:
                    # Dependiendo de cómo envíes el form, puede que vengan muchos
                    # Archivos "photos_container_closed" o que vengan en un array con un nombre distinto.
                    # Ejemplo, si los subes con "photos_container_closed.add" = [File1, File2],
                    # DRF no lo parsea nativamente como tu JSON.
                    #
                    # Lo más sencillo es usar un approach en front de “campo repetido”
                    # o un FormData con “photos_container_closed” repetido.
                    # Ajusta según tu estructura.
                    files_to_add = request.FILES.getlist(field_name)
                    for fobj in files_to_add:
                        doc = create_documento(fobj, fobj.name, "Claim", claim.claim_code)
                        m2m_relation.add(doc)

                # Si tu JSON con “add” no viaja en la parte de FILES sino como otra cosa,
                # habría que ajustarlo. Normalmente, “add” lo esperas en request.FILES.

        claim.save()

        # 4. Actualizar ClaimProducts
        # Se espera algo como:
        # "products": [
        #   { "id": 100, "product": "...", "quantity": 2, "batch": "...", "_delete": false },
        #   { "id": 101, "product": "...", "quantity": 5, "batch": "...", "_delete": true },
        #   { "product": "...", "quantity": 3, "batch": "nuevo" }
        # ]
        #
        # Donde `id` es el ID del ClaimProduct y `_delete` indica si borrarlo.
        # `product` podría ser un ID de “product” real, o un simple texto, depende de tu modelado.
        #
        # Adicionalmente, tu ClaimProduct puede tener su propio ViewSet, pero si prefieres
        # manejarlo central aquí, sin anidar serializers, se puede hacer como sigue:
        from apps.imported.model import ClaimProductModel

        products_data = data.get("products", [])
        for p in products_data:
            product_id = p.get("id")  # ID del ClaimProduct
            delete_flag = p.get("_delete", False)

            if product_id:
                # ClaimProduct existente
                try:
                    cp = ClaimProductModel.objects.get(pk=product_id, claim=claim)
                except ClaimProductModel.DoesNotExist:
                    continue  # O devuelves un error, depende.

                if delete_flag:
                    cp.delete()
                    continue

                # Actualizar
                cp.product_name = p.get("product", cp.product_name)
                cp.quantity = p.get("quantity", cp.quantity)
                cp.batch = p.get("batch", cp.batch)
                cp.save()
            else:
                # Nuevo ClaimProduct
                if not delete_flag:
                    new_cp = ClaimProductModel.objects.create(
                        claim=claim,
                        product_name=p.get("product", ""),
                        quantity=p.get("quantity", 0),
                        batch=p.get("batch", ""),
                    )
                    new_cp.save()

        # Al final, serializas y devuelves el reclamo
        serializer = self.get_serializer(claim)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Vista de productos asociados a un reclamo
class ClaimProductViewSet(mixins.ListModelMixin, viewsets.GenericViewSet,
                          mixins.CreateModelMixin, mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin):
    """
    ViewSet para manejar los productos asociados a un reclamo.
    """
    queryset = ClaimProductModel.objects.all()
    serializer_class = ClaimProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["claim"]
    search_fields = ["claim__description", "product__name"]
    ordering_fields = ["claim__created_at", "product__name"]
    ordering = ["claim__created_at"]
    permission_classes = []

    PERMISSION_MAPPING = {
        "GET": ["claims.view_reclamomodel"],
        "POST": ["claims.add_reclamomodel"],
        "PUT": ["claims.change_reclamomodel"],
        "PATCH": ["claims.change_reclamomodel"],
        "DELETE": ["claims.delete_reclamomodel"],
    }

    # Puedes agregar permisos específicos aquí si lo deseas
    def get_permissions(self):
        # Aquí podrías integrar tu CustomAccessPermission si lo deseas.
        return super().get_permissions()
    #     def get_queryset(self):
