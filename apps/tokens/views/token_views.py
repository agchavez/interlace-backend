"""
ViewSet principal para TokenRequest
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse

from ..models import TokenRequest
from ..serializers import (
    TokenRequestListSerializer,
    TokenRequestDetailSerializer,
    TokenRequestCreateSerializer,
    TokenApprovalSerializer,
    TokenRejectSerializer,
    TokenValidateSerializer,
    PublicTokenSerializer,
)
from ..permissions import (
    CanRequestTokens,
    CanApproveTokenL1,
    CanApproveTokenL2,
    CanApproveTokenL3,
    CanValidateToken,
    IsTokenOwnerOrApprover,
)
from ..filters import TokenRequestFilter
from ..utils import generate_token_qr, TokenNotificationHelper, generate_token_pdf, generate_token_receipt
from ..services.approval_service import ApprovalLevelService
from apps.personnel.models import PersonnelProfile


class TokenRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de tokens.

    Endpoints:
    - GET /api/tokens/ - Listar tokens (con filtros)
    - POST /api/tokens/ - Crear nuevo token
    - GET /api/tokens/{id}/ - Detalle de token
    - PUT/PATCH /api/tokens/{id}/ - Actualizar token (solo borrador)
    - DELETE /api/tokens/{id}/ - Eliminar token (solo borrador)

    Actions:
    - POST /api/tokens/{id}/approve_l1/ - Aprobar nivel 1
    - POST /api/tokens/{id}/approve_l2/ - Aprobar nivel 2
    - POST /api/tokens/{id}/approve_l3/ - Aprobar nivel 3
    - POST /api/tokens/{id}/reject/ - Rechazar token
    - POST /api/tokens/{id}/cancel/ - Cancelar token
    - POST /api/tokens/validate/ - Validar token por QR (Seguridad)
    - GET /api/tokens/pending_my_approval/ - Tokens pendientes de mi aprobación
    - GET /api/tokens/my_tokens/ - Mis tokens (como beneficiario o solicitante)
    """
    queryset = TokenRequest.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TokenRequestFilter
    search_fields = ['display_number', 'personnel__first_name', 'personnel__last_name', 'personnel__employee_code']
    ordering_fields = ['created_at', 'valid_from', 'valid_until', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TokenRequestListSerializer
        if self.action == 'create':
            return TokenRequestCreateSerializer
        if self.action in ['approve_l1', 'approve_l2', 'approve_l3']:
            return TokenApprovalSerializer
        if self.action == 'reject':
            return TokenRejectSerializer
        return TokenRequestDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanRequestTokens()]
        if self.action == 'approve_l1':
            return [IsAuthenticated(), CanApproveTokenL1()]
        if self.action == 'approve_l2':
            return [IsAuthenticated(), CanApproveTokenL2()]
        if self.action == 'approve_l3':
            return [IsAuthenticated(), CanApproveTokenL3()]
        if self.action == 'validate':
            return [IsAuthenticated(), CanValidateToken()]
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTokenOwnerOrApprover()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filtrar tokens según permisos del usuario"""
        user = self.request.user
        qs = TokenRequest.objects.select_related(
            'personnel', 'personnel__area',
            'requested_by',
            'distributor_center',
            'approved_level_1_by',
            'approved_level_2_by',
            'approved_level_3_by',
            'rejected_by',
            'validated_by',
        )

        if user.is_superuser or user.is_staff:
            return qs

        try:
            personnel = user.personnel_profile
        except:
            return qs.none()

        # Filtrar por centro de distribución del usuario
        user_centers = list(user.distributions_centers.values_list('id', flat=True))
        if user.centro_distribucion:
            user_centers.append(user.centro_distribucion.id)

        return qs.filter(distributor_center_id__in=user_centers)

    def create(self, request, *args, **kwargs):
        """Crear token, generar QR y devolver detalle completo"""
        from django.utils import timezone

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.save(requested_by=request.user)

        # Verificar auto-aprobación
        try:
            requester_profile = request.user.personnel_profile
            beneficiary_profile = token.personnel

            if beneficiary_profile and ApprovalLevelService.can_auto_approve(
                requester_profile, beneficiary_profile
            ):
                # Auto-aprobar todos los niveles requeridos
                if token.requires_level_1 and not token.approved_level_1_at:
                    token.approved_level_1_by = requester_profile
                    token.approved_level_1_at = timezone.now()
                    token.approved_level_1_notes = "Auto-aprobado por jerarquía superior"

                if token.requires_level_2 and not token.approved_level_2_at:
                    token.approved_level_2_by = requester_profile
                    token.approved_level_2_at = timezone.now()
                    token.approved_level_2_notes = "Auto-aprobado por jerarquía superior"

                if token.requires_level_3 and not token.approved_level_3_at:
                    token.approved_level_3_by = requester_profile
                    token.approved_level_3_at = timezone.now()
                    token.approved_level_3_notes = "Auto-aprobado por jerarquía superior"

                token.status = TokenRequest.Status.APPROVED
                token.save()

                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Token {token.display_number} auto-aprobado por {requester_profile.full_name} "
                    f"(jerarquía: {requester_profile.hierarchy_level})"
                )

        except PersonnelProfile.DoesNotExist:
            pass

        # Generar código QR
        try:
            qr_url = generate_token_qr(token)
            token.qr_code_url = qr_url
            token.save(update_fields=['qr_code_url'])
        except Exception as e:
            # Log error but don't fail the creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando QR para token {token.id}: {e}")

        # Enviar notificación al siguiente aprobador (solo si no fue auto-aprobado)
        if token.status != TokenRequest.Status.APPROVED:
            TokenNotificationHelper.notify_pending_approval(token)

        # Return detail serializer with id and all fields
        detail_serializer = TokenRequestDetailSerializer(token)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve_l1(self, request, pk=None):
        """
        Aprobar token en nivel 1.
        Acepta multipart/form-data con firma y foto opcionales.
        """
        token = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            personnel = request.user.personnel_profile
            token.approve_level_1(
                personnel,
                notes=serializer.validated_data.get('notes', ''),
                signature=serializer.validated_data.get('signature'),
                photo=serializer.validated_data.get('photo')
            )

            # Notificar aprobación
            TokenNotificationHelper.notify_token_approved(token, 1)

            # Si hay más niveles, notificar al siguiente aprobador
            if token.status in [TokenRequest.Status.PENDING_L2, TokenRequest.Status.PENDING_L3]:
                TokenNotificationHelper.notify_pending_approval(token)

            return Response(TokenRequestDetailSerializer(token).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve_l2(self, request, pk=None):
        """
        Aprobar token en nivel 2.
        Acepta multipart/form-data con firma y foto opcionales.
        """
        token = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            personnel = request.user.personnel_profile
            token.approve_level_2(
                personnel,
                notes=serializer.validated_data.get('notes', ''),
                signature=serializer.validated_data.get('signature'),
                photo=serializer.validated_data.get('photo')
            )

            # Notificar aprobación
            TokenNotificationHelper.notify_token_approved(token, 2)

            # Si hay más niveles, notificar al siguiente aprobador
            if token.status == TokenRequest.Status.PENDING_L3:
                TokenNotificationHelper.notify_pending_approval(token)

            return Response(TokenRequestDetailSerializer(token).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve_l3(self, request, pk=None):
        """
        Aprobar token en nivel 3.
        Acepta multipart/form-data con firma y foto opcionales.
        """
        token = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            personnel = request.user.personnel_profile
            token.approve_level_3(
                personnel,
                notes=serializer.validated_data.get('notes', ''),
                signature=serializer.validated_data.get('signature'),
                photo=serializer.validated_data.get('photo')
            )

            # Notificar aprobación final
            TokenNotificationHelper.notify_token_approved(token, 3)

            return Response(TokenRequestDetailSerializer(token).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar token"""
        token = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            personnel = request.user.personnel_profile
            token.reject(personnel, serializer.validated_data['reason'])

            # Notificar rechazo
            TokenNotificationHelper.notify_token_rejected(token)

            return Response(TokenRequestDetailSerializer(token).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar token"""
        token = self.get_object()

        try:
            token.cancel()
            return Response(TokenRequestDetailSerializer(token).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Validar token para marcarlo como USED.
        - EXIT_PASS, PERMIT_HOUR: validados por Seguridad
        - RATE_CHANGE, SUBSTITUTION: validados por Planilla
        Los demás tipos (PERMIT_DAY, OVERTIME, SHIFT_CHANGE) se quedan en APPROVED.
        Acepta multipart/form-data con firma y foto opcionales.
        Espera: { "token_code": "uuid-del-token", "notes"?: "", "signature"?: File, "photo"?: File }
        """
        serializer = TokenValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_code = serializer.validated_data.get('token_code')
        token = get_object_or_404(TokenRequest, token_code=token_code)

        # Verificar si el tipo de token requiere validación
        if not token.requires_validation:
            return Response(
                {'error': f'Este tipo de token ({token.get_token_type_display()}) no requiere validación. Se queda en estado Aprobado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos según tipo de validación
        validation_type = token.validation_type
        user = request.user

        if validation_type == 'security':
            # Validar que el usuario tenga permiso de seguridad (portería)
            if not user.has_perm('tokens.can_validate_token'):
                return Response(
                    {'error': 'No tiene permisos para validar tokens de seguridad.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif validation_type == 'payroll':
            # Validar que el usuario tenga permiso de planilla
            if not user.has_perm('tokens.can_validate_payroll'):
                return Response(
                    {'error': 'No tiene permisos para marcar tokens como utilizados (Planilla).'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if not token.can_be_used:
            if token.status != TokenRequest.Status.APPROVED:
                return Response(
                    {'error': f'El token no está aprobado. Estado actual: {token.get_status_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not token.is_valid:
                return Response(
                    {'error': 'El token está fuera del período de vigencia'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            personnel = request.user.personnel_profile
            token.mark_as_used(
                validated_by=personnel,
                signature=serializer.validated_data.get('signature'),
                photo=serializer.validated_data.get('photo'),
                notes=serializer.validated_data.get('notes', '')
            )

            # Notificar que fue utilizado (excluyendo al usuario que validó)
            TokenNotificationHelper.notify_token_used(token, used_by_user=request.user)

            return Response(TokenRequestDetailSerializer(token).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def pending_my_approval(self, request):
        """Obtener tokens pendientes de aprobación para el usuario actual"""
        try:
            personnel = request.user.personnel_profile
        except:
            return Response([])

        qs = self.get_queryset()

        # Filtrar según nivel de aprobación del usuario
        if personnel.can_approve_tokens_level_3():
            qs = qs.filter(
                Q(status=TokenRequest.Status.PENDING_L1) |
                Q(status=TokenRequest.Status.PENDING_L2) |
                Q(status=TokenRequest.Status.PENDING_L3)
            )
        elif personnel.can_approve_tokens_level_2():
            qs = qs.filter(
                Q(status=TokenRequest.Status.PENDING_L1) |
                Q(status=TokenRequest.Status.PENDING_L2)
            )
        elif personnel.can_approve_tokens_level_1():
            qs = qs.filter(status=TokenRequest.Status.PENDING_L1)
        else:
            return Response([])

        # Excluir tokens donde el usuario es el beneficiario (no puede aprobar su propio token)
        qs = qs.exclude(personnel=personnel)

        serializer = TokenRequestListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_tokens(self, request):
        """Obtener tokens donde el usuario es beneficiario o solicitante"""
        user = request.user
        qs = self.get_queryset()

        try:
            personnel = user.personnel_profile
            qs = qs.filter(
                Q(personnel=personnel) | Q(requested_by=user)
            )
        except:
            qs = qs.filter(requested_by=user)

        serializer = TokenRequestListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_code/(?P<code>[^/.]+)')
    def by_code(self, request, code=None):
        """
        Buscar token por display_number (TK-2026-000001) o token_code (UUID).
        Usado en la página de validación para buscar tokens.
        """
        if not code:
            return Response(
                {'error': 'Se requiere el código del token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Intentar buscar por display_number primero (más común)
        token = TokenRequest.objects.filter(display_number__iexact=code).first()

        # Si no se encuentra, intentar por token_code (UUID)
        if not token:
            token = TokenRequest.objects.filter(token_code=code).first()

        if not token:
            return Response(
                {'error': 'Token no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Devolver datos para validación (similar a public pero con más info)
        serializer = PublicTokenSerializer(token)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """
        Descargar el token como documento PDF.
        GET /api/tokens/{id}/download_pdf/
        """
        token = self.get_object()

        try:
            pdf_buffer = generate_token_pdf(token)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="token_{token.display_number}.pdf"'
            return response
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando PDF para token {token.id}: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return Response(
                {'error': 'Error al generar el documento PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download_receipt(self, request, pk=None):
        """
        Descargar recibo tipo ticket (80mm) para impresora térmica.
        Solo disponible cuando el token está APPROVED o USED.
        GET /api/tokens/{id}/download_receipt/?copy=true para copia
        GET /api/tokens/{id}/download_receipt/ para original
        """
        token = self.get_object()

        # Verificar estado del token
        allowed_states = [TokenRequest.Status.APPROVED, TokenRequest.Status.USED]
        if token.status not in allowed_states:
            return Response(
                {'error': f'El recibo solo está disponible para tokens aprobados o utilizados. Estado actual: {token.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determinar si es copia u original
        is_copy = request.query_params.get('copy', '').lower() in ['true', '1', 'yes']

        try:
            receipt_buffer = generate_token_receipt(token, is_copy=is_copy)
            response = HttpResponse(receipt_buffer.getvalue(), content_type='application/pdf')
            suffix = '_copia' if is_copy else ''
            response['Content-Disposition'] = f'attachment; filename="recibo_{token.display_number}{suffix}.pdf"'
            return response
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando recibo para token {token.id}: {e}")
            return Response(
                {'error': 'Error al generar el recibo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pending_validation(self, request):
        """
        Obtener tokens aprobados pendientes de validación (para Seguridad).
        Solo tokens APPROVED que están dentro del período de vigencia.
        GET /api/tokens/pending_validation/
        """
        from django.utils import timezone

        qs = self.get_queryset().filter(
            status=TokenRequest.Status.APPROVED,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now(),
        ).order_by('valid_until')  # Ordenar por los que expiran primero

        serializer = TokenRequestListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_uniform_delivery(self, request, pk=None):
        """
        Completar la entrega de uniforme con foto y firma.
        POST /api/tokens/{id}/complete_uniform_delivery/

        Expected data (multipart/form-data):
        - signature: image file (required)
        - photo_1: image file (optional)
        - photo_2: image file (optional)
        - notes: string (optional)
        """
        token = self.get_object()

        # Validar que sea un token de entrega de uniforme
        if token.token_type != TokenRequest.TokenType.UNIFORM_DELIVERY:
            return Response(
                {'error': 'Este token no es de entrega de uniforme'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que el token esté aprobado
        if token.status != TokenRequest.Status.APPROVED:
            return Response(
                {'error': f'El token debe estar aprobado. Estado actual: {token.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que tenga detalle de uniforme
        if not hasattr(token, 'uniform_delivery_detail'):
            return Response(
                {'error': 'Token sin detalle de uniforme'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que no esté ya entregado
        if token.uniform_delivery_detail.is_delivered:
            return Response(
                {'error': 'Este uniforme ya fue entregado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener datos
        signature = request.FILES.get('signature')
        photo_1 = request.FILES.get('photo_1')
        photo_2 = request.FILES.get('photo_2')
        notes = request.data.get('notes', '')

        # Validar firma
        if not signature:
            return Response(
                {'error': 'Se requiere la firma del beneficiario'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            personnel = request.user.personnel_profile
        except:
            return Response(
                {'error': 'Usuario sin perfil de personal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Completar la entrega
        try:
            token.uniform_delivery_detail.mark_as_delivered(
                delivered_by=personnel,
                signature=signature,
                photo1=photo_1,
                photo2=photo_2,
                notes=notes
            )

            # Marcar el token como usado
            token.mark_as_used(personnel)

            # Notificar (excluyendo al usuario que completó la entrega)
            TokenNotificationHelper.notify_token_used(token, used_by_user=request.user)

            return Response(TokenRequestDetailSerializer(token).data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completando entrega de uniforme {token.id}: {e}")
            return Response(
                {'error': 'Error al completar la entrega'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
