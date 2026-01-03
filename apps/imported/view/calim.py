from django.utils import timezone
from rest_framework import mixins, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.document.utils.documents import create_documento
from apps.imported.exceptions.claim import ClaimTypeInvalid
from apps.imported.model import ClaimProductModel
from apps.imported.model.claim import ClaimModel, ClaimTypeModel
from apps.imported.serializers import ClaimProductSerializer, ClaimTypeSerializer
from apps.imported.serializers.claim import ClaimSerializer
from apps.imported.utils.claim import create_reclamo, change_reclamo_state
from apps.imported.utils.validation_claim import validate_create_claim
from django_filters import rest_framework as django_filters
from django.db.models import Q
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from django.http import FileResponse
import io
import json

from apps.user.models.notificacion import NotificationModel

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.user.models import UserModel
from apps.user.serializers.notificacion import NotificationSerializer

class ClaimFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    status = django_filters.CharFilter()
    tipo = django_filters.NumberFilter(field_name='claim_type', lookup_expr='exact')
    distributor_center = django_filters.NumberFilter(field_name='tracker__distributor_center__id')
    date_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    claim_type = django_filters.CharFilter(method='filter_claim_type_custom')

    class Meta:
        model = ClaimModel  # Reemplaza con tu modelo real
        fields = ['id', 'status', 'tipo', 'distributor_center', 'date_after', 'date_before', 'claim_type']

    def filter_claim_type_custom(self, queryset, name, value):
        if value == "LOCAL":
            return queryset.filter(tracker__type="LOCAL")
        elif value == "IMPORT":
            return queryset.filter(tracker__type="IMPORT")
        return queryset

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
    search_fields = ["claim_type", "description", "tracker__distributor_center__name"]
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
        changes = {}
        tracker_id = request.data.get("tracker_id")

        # Validamos los datos del request usando nuestra nueva utilidad
        user, tracker, _ = validate_create_claim(request, tracker_id=int(tracker_id))

        # Extraemos los datos del request
        assigned_user_id = request.data.get("assigned_user_id")
        claim_type = request.data.get("claim_type")
        claim_type = ClaimTypeModel.objects.filter(id=int(claim_type)).first()
        descripcion = request.data.get("descripcion")

        # Campos adicionales
        claim_number = request.data.get("claim_number")
        discard_doc = request.data.get("discard_doc")
        observations = request.data.get("observations")

        # Archivos de documentos
        claim_file = request.FILES.get("claim_file") if "claim_file" in request.FILES else None
        credit_memo_file = request.FILES.get("credit_memo_file") if "credit_memo_file" in request.FILES else None
        observations_file = request.FILES.get("observations_file") if "observations_file" in request.FILES else None
        # Fotografías por categoría
        photo_files = {}
        photo_categories = [
            "photos_container_closed", "photos_container_one_open",
            "photos_container_two_open", "photos_container_top",
            "photos_during_unload", "photos_pallet_damage",
            "photos_damaged_product_base", "photos_damaged_product_dents",
            "photos_damaged_boxes", "photos_grouped_bad_product",
            "photos_repalletized", "photos_production_batch"
        ]

        photo_categories_verbose = {
            "photos_container_closed": "Foto Contenedor cerrado",
            "photos_container_one_open": "Foto Contenedor con 1 puerta abierta",
            "photos_container_two_open": "Foto Contenedor con 2 puertas abiertas",
            "photos_container_top": "Foto Vista superior del contenedor",
            "photos_during_unload": "Foto Durante la descarga",
            "photos_pallet_damage": "Foto Fisuras/abolladuras de pallets",
            "photos_damaged_product_base": "Foto Base de producto dañado",
            "photos_damaged_product_dents": "Foto Abolladuras del producto",
            "photos_damaged_boxes": "Foto Cajas dañadas",
            "photos_grouped_bad_product": "Foto Producto en mal estado agrupado",
            "photos_repalletized": "Foto Repaletizado de producto dañado",
            "photos_production_batch": "Foto Lote de producción"
        }

        for category in photo_categories:
            if category in request.FILES:
                photo_files[category] = request.FILES.getlist(category)
                cuenta = 0
                for doc in photo_files[category]:
                    cuenta += 1
                    changes[f'{photo_categories_verbose.get(category, "Foto")} #{cuenta}'] = f'nombre: {doc.name}'

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

        # Guardar productos
        from apps.imported.model import ClaimProductModel
        raw_products_str = request.data.get("products", "[]")

        try:
            products_data = json.loads(raw_products_str)
        except json.JSONDecodeError:
            products_data = []

        for p in products_data:
            product_id = p.get("id")
            if product_id:
                try:
                    cp = ClaimProductModel.objects.get(pk=product_id, claim=reclamo)
                except ClaimProductModel.DoesNotExist:
                    continue

                cp.product_id = p.get("product", cp.product)
                cp.quantity = p.get("quantity", cp.quantity)
                cp.batch = p.get("batch", cp.batch)
                cp.save()
                changes[f'Actualizado: {cp.product.name}'] = f"cantidad: {cp.quantity}, lote: {cp.batch}"
            else:
                if not ClaimProductModel.objects.filter(
                        claim=reclamo,
                        product_id=p.get("product", "")
                ).exists():
                    ClaimProductModel.objects.create(
                        claim=reclamo,
                        product_id=p.get("product", ""),
                        quantity=p.get("quantity", 0),
                        batch=p.get("batch", ""),
                    )
                    changes[f'Agregado: {cp.product.name}'] = f'cantidad: {cp.quantity}, lote: {cp.batch}'

        # Notificación
        if reclamo.type == "CLAIM":
            self.send_notification(
                title="Nuevo Claim", 
                subtitle='Se ha registrado un nuevo claim', 
                description='Se ha registrado un nuevo claim sobre el tracker ' + str(reclamo.tracker.pk), 
                reclamo=reclamo,
                json={
                    'tracker': reclamo.tracker.pk,
                    'Tipo de Reclamo': reclamo.claim_type.name if reclamo.claim_type else None,
                    "Descripción": reclamo.description,
                    "Numero de Reclamo": reclamo.claim_number,
                    "Observaciones": reclamo.observations,
                    "Documento de Descarte": reclamo.discard_doc,
                    "Archivo Claim": reclamo.claim_file.name if reclamo.claim_file else None,
                    "Archivo Nota de Crédito": reclamo.credit_memo_file.name if reclamo.credit_memo_file else None,
                    "Archivo Observaciones": reclamo.observations_file.name if reclamo.observations_file else None,
                    **changes
                })
        serializer = self.get_serializer(reclamo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def send_notification(self, title, subtitle, description, reclamo, json: dict = None):
        """
        Envia una notificación a los usuarios de tipo Claim Service User.
        """
        users = UserModel.objects.filter(is_active=True, groups__id=5, distributions_centers__id=reclamo.tracker.distributor_center.id)
        for user in users:
            notification = NotificationModel.objects.create(
                user=user,
                type=NotificationModel.Type.CLAIM,
                title=title,
                subtitle=subtitle,
                description=description,
                module=NotificationModel.Modules.OTHERS,
                url=f'/claim/editstatus/{reclamo.id}' if reclamo else None,
                json=json
            )
            # Enviar notificación a través de websocket
            group_name = str(user.id)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'data': NotificationSerializer(notification).data
                }
            )

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
            "photos_repalletized", "photos_production_batch"
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
            "photos_repalletized": claim.photos_repalletized,
            "photos_production_batch": claim.photos_production_batch
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
            "photos_repalletized": "Repaletizado de producto dañado",
            "photos_production_batch": "Lote de producción"
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
        changes = {}
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
            changes["Estado del Reclamo"] = reclamo.status
        except ClaimModel.DoesNotExist:
            return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Claim Number
        if "new_claim_number" in request.data:
            claim_number = request.data.get("new_claim_number")
            try:
                reclamo.claim_number = claim_number
                reclamo.save()
                changes["Numero de Reclamo"] = reclamo.claim_number
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        # Discard Doc
        if "new_discard_doc" in request.data:
            discard_doc = request.data.get("new_discard_doc")
            try:
                reclamo.discard_doc = discard_doc
                reclamo.save()
                changes["Documento de Descarte"] = reclamo.discard_doc
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        # Observations
        if "new_observations" in request.data:
            observations = request.data.get("new_observations")
            try:
                reclamo.observations = observations
                reclamo.save()
                changes["Observaciones"] = reclamo.observations
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Aprove Observations
        if "new_approve_observations" in request.data:
            approve_observations = request.data.get("new_approve_observations")
            try:
                reclamo.approve_observations = approve_observations
                reclamo.save()
                changes["Observaciones de Aprobación"] = reclamo.approve_observations
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Reject Reason
        if "reject_reason" in request.data:
            reject_reason = request.data.get("reject_reason")
            try:
                reclamo.reject_reason = reject_reason
                reclamo.save()
                changes["Razón de Rechazo"] = reclamo.reject_reason
            except ClaimModel.DoesNotExist:
                return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Claim File
        new_claim_file = request.FILES.get("new_claim_file")
        if new_claim_file:
            # En lugar de asignar directamente, usar create_documento()
            doc_claim = create_documento(new_claim_file,new_claim_file.name,  "Claim", reclamo.claim_code)
            reclamo.claim_file = doc_claim.file
            changes["Archivo Claim"] = doc_claim.file.name

        # Claim Credit Memo File
        new_credit_memo_file = request.FILES.get("new_credit_memo_file")
        if new_credit_memo_file:
            doc_credit = create_documento(new_credit_memo_file, new_credit_memo_file.name, "Claim", reclamo.claim_code)
            reclamo.credit_memo_file = doc_credit.file
            changes["Archivo Nota de Crédito"] = doc_credit.file.name

        # Claim Observations File
        new_observations_file = request.FILES.get("new_observations_file")
        if new_observations_file:
            doc_obs = create_documento(new_observations_file, new_observations_file.name, "Claim", reclamo.claim_code)
            reclamo.observations_file = doc_obs.file
            changes["Archivo Observaciones"] = doc_obs.file.name

        reclamo.save()

        # Notificación
        if reclamo.type == "CLAIM":
            self.send_notification(
                title="Cambio de estado en claim",
                subtitle='Se ha realizado un cambio de estado en el claim ',
                description='Cambio de estado en el claim ' + str(reclamo.pk) + ' a ' + reclamo.status,
                reclamo=reclamo,
                json={
                    **changes
                })

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
        if request.query_params.get('id'):
            filters['id'] = request.query_params.get('id')
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
        claim_type = request.query_params.get('claim_type')
        if claim_type:
            if claim_type == "LOCAL":
                filters['tracker__type'] = "LOCAL"
            elif claim_type == "IMPORT":
                filters['tracker__type'] = "IMPORT"
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
        for photo in reclamo.photos_production_batch.all():
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
            claim = self.get_object()
        except ClaimModel.DoesNotExist:
            return Response({"detail": "Claim no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        changes = {}

        data = request.data

        # 1) Actualizar campos principales
        claim_type = data.get("claim_type", claim.claim_type)
        claim_type = ClaimTypeModel.objects.filter(id=claim_type).first()
        if claim_type is not None:
            claim.claim_type = claim_type
            if claim_type.name != claim.claim_type.name:
                changes["Tipo de Reclamo"] = claim_type.name
        description = data.get("description", claim.description)
        if description != claim.description:
            changes["Descripción"] = description
        claim_number = data.get("claim_number", claim.claim_number)
        if claim_number != claim.claim_number:
            changes["Numero de Reclamo"] = claim_number
        discard_doc = data.get("discard_doc", claim.discard_doc)
        if discard_doc != claim.discard_doc:
            changes["Documento de Descarte"] = discard_doc
        observations = data.get("observations", claim.observations)
        if observations != claim.observations:
            changes["Observaciones"] = observations

        claim.description = description
        claim.claim_number = claim_number
        claim.discard_doc = discard_doc
        claim.observations = observations

        # 2) Actualizar archivos principales
        if "claim_file" in request.FILES:
            f = request.FILES["claim_file"]
            doc_claim = create_documento(f, f.name, "Claim", claim.claim_code)
            claim.claim_file = doc_claim.file
            changes["Archivo Claim"] = doc_claim.file.name
        # elif data.get("claim_file") is None:
        #     claim.claim_file = None

        if "credit_memo_file" in request.FILES:
            f = request.FILES["credit_memo_file"]
            doc_credit = create_documento(f, f.name, "Claim", claim.claim_code)
            claim.credit_memo_file = doc_credit.file
            changes["Archivo Nota de Crédito"] = doc_credit.file.name
        # elif data.get("credit_memo_file") is None:
        #     claim.credit_memo_file = None

        if "observations_file" in request.FILES:
            f = request.FILES["observations_file"]
            doc_obs = create_documento(f, f.name, "Claim", claim.claim_code)
            claim.observations_file = doc_obs.file
            changes["Archivo Observaciones"] = doc_obs.file.name


        claim.save()

        # 3) Actualizar fotos M2M
        #    Usamos 2 llaves por cada categoría:
        #    Ej: "photos_container_closed_meta" para la metadata JSON,
        #        "photos_container_closed" para los archivos.
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
            "photos_production_batch": claim.photos_production_batch
        }

        photo_fields_verbose = {
            "photos_container_closed": "Foto Contenedor cerrado",
            "photos_container_one_open": "Foto Contenedor con 1 puerta abierta",
            "photos_container_two_open": "Foto Contenedor con 2 puertas abiertas",
            "photos_container_top": "Foto Vista superior del contenedor",
            "photos_during_unload": "Foto Durante la descarga",
            "photos_pallet_damage": "Foto Fisuras/abolladuras de pallets",
            "photos_damaged_product_base": "Foto Base de producto dañado",
            "photos_damaged_product_dents": "Foto Abolladuras del producto",
            "photos_damaged_boxes": "Foto Cajas dañadas",
            "photos_grouped_bad_product": "Foto Producto en mal estado agrupado",
            "photos_repalletized": "Foto Repaletizado de producto dañado",
            "photos_production_batch": "Foto Lote de producción"
        }


        for field_name, m2m_relation in photo_fields.items():
            meta_key = f"{field_name}_meta"  # "photos_container_closed_meta", etc.

            cat_data = {"remove": []}
            if meta_key in data:
                cat_data_str = data[meta_key]
                try:
                    cat_data = json.loads(cat_data_str)  # parse => dict
                except json.JSONDecodeError:
                    cat_data = {"remove": []}

            # a) Eliminar
            to_remove = cat_data.get("remove", [])
            if to_remove:
                m2m_relation.remove(*to_remove)
                for doc in to_remove:
                    changes[f'Eliminado {photo_fields_verbose.get(field_name, "Foto")} id: {doc}'] = f'Archivo Eliminado'

            # b) Agregar => usando request.FILES.getlist(field_name)
            if field_name in request.FILES:
                files_to_add = request.FILES.getlist(field_name)
                cuenta = 0
                for fobj in files_to_add:
                    cuenta += 1
                    doc = create_documento(fobj, fobj.name, "Claim", claim.claim_code)
                    m2m_relation.add(doc)
                    changes[f'Agregado {photo_fields_verbose.get(field_name, "Foto")} #{cuenta}'] = f'nombre: {doc.name}'

        claim.save()

        # 4) Actualizar ClaimProducts
        from apps.imported.model import ClaimProductModel
        raw_products_str = data.get("products", "[]")
        try:
            products_data = json.loads(raw_products_str)
        except json.JSONDecodeError:
            products_data = []

        for p in products_data:
            product_id = p.get("id")
            delete_flag = p.get("_delete", False)
            if product_id:
                try:
                    cp = ClaimProductModel.objects.get(pk=product_id, claim=claim)
                except ClaimProductModel.DoesNotExist:
                    continue

                if delete_flag:
                    cp.delete()
                    changes[f'Eliminado: {cp.product.name}'] = "Producto Eliminado del Reclamo"
                    continue
                cp.product_id = p.get("product", cp.product)
                initial_quantity = cp.quantity
                initial_batch = cp.batch
                cp.quantity = p.get("quantity", cp.quantity)
                cp.batch = p.get("batch", cp.batch)
                if initial_quantity != cp.quantity or initial_batch != cp.batch:
                    changes[f'Actualizado: {cp.product.name}'] = f"cantidad inicial: {initial_quantity}, cantidad actualizada: {cp.quantity}, lote inicial: {initial_batch}, lote actualizado: {cp.batch}"
                cp.save()
            else:
                if not delete_flag:
                    if not ClaimProductModel.objects.filter(
                            claim=claim,
                            product_id=p.get("product", "")
                    ).exists():
                        cp = ClaimProductModel.objects.create(
                            claim=claim,
                            product_id=p.get("product", ""),
                            quantity=p.get("quantity", 0),
                            batch=p.get("batch", ""),
                        )
                        changes[f'Agregado: {cp.product.name}'] = f'cantidad: {cp.quantity}, lote: {cp.batch}'

        # Notificación
        if claim.type == "CLAIM":
            # si changes no es vacío, se envia notificación
            changes_keys = list(changes.keys())
            if (len(changes_keys) > 0):
                self.send_notification(
                    title="Actualización de claim",
                    subtitle='Se ha actualizado el claim ',
                    description='Se ha actualizado el claim con id ' + str(claim.pk),
                    reclamo=claim,
                    json={
                        **changes
                    })

        # 5) Serializar y devolver
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


# Vista de tipos de reclamos
class ClaimTypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet,
                        mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin):
    """
    ViewSet para manejar los tipos de reclamos.
    """
    queryset = ClaimTypeModel.objects.all()
    serializer_class = ClaimTypeSerializer
    permission_classes = []
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["id"]
    search_fields = ["name", "id"]
