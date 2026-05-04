"""
Endpoints del módulo Reempaque.

Flujo principal:
  1. POST /api/repack-session/start/        → crea sesión (operario inicia)
  2. POST /api/repack-entry/                → digita lotes (`box_count>0`) o
                                              ajustes (`box_count<0`) — la
                                              métrica por hora se actualiza
                                              en vivo al guardar.
  3. POST /api/repack-session/<id>/finish/  → cierra sesión y emite el
                                              sample agregado del turno.

Lecturas:
  GET /api/repack-session/active/           → sesión activa del usuario actual
  GET /api/repack-session/?...              → historial filtrable
  GET /api/repack-session/<id>/             → detalle con entries
"""
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .metrics import on_entry_changed, on_session_finished
from .models import RepackEntry, RepackSession
from .serializers import (
    RepackEntrySerializer,
    RepackSessionDetailSerializer,
    RepackSessionListSerializer,
)


def _get_user_dc(user):
    """CD activo del usuario (centro_distribucion en User o primary del perfil)."""
    if getattr(user, 'centro_distribucion_id', None):
        return user.centro_distribucion
    profile = getattr(user, 'personnel_profile', None)
    return profile.primary_distributor_center if profile else None


def _get_user_personnel(user):
    return getattr(user, 'personnel_profile', None)


class RepackSessionViewSet(viewsets.ModelViewSet):
    """Sesiones de reempaque. Filtra siempre por CD del usuario."""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['personnel', 'operational_date', 'status', 'distributor_center']

    def get_serializer_class(self):
        if self.action == 'list':
            return RepackSessionListSerializer
        return RepackSessionDetailSerializer

    def get_queryset(self):
        dc = _get_user_dc(self.request.user)
        qs = RepackSession.objects.select_related('personnel', 'distributor_center').prefetch_related('entries')
        if dc:
            qs = qs.filter(distributor_center=dc)
        return qs

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Inicia una sesión nueva para el operario actual (o el `personnel_id`
        que se mande, en caso de que un supervisor la inicie por él)."""
        dc = _get_user_dc(request.user)
        if not dc:
            return Response({'error': 'Usuario sin CD asignado.'}, status=status.HTTP_400_BAD_REQUEST)

        personnel_id = request.data.get('personnel_id')
        if personnel_id:
            from apps.personnel.models.personnel import PersonnelProfile
            try:
                personnel = PersonnelProfile.objects.get(pk=personnel_id, is_active=True)
            except PersonnelProfile.DoesNotExist:
                return Response({'error': 'Operario no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            personnel = _get_user_personnel(request.user)
            if not personnel:
                return Response(
                    {'error': 'El usuario no tiene perfil de personal.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # No permitir dos sesiones activas simultáneas para el mismo operario.
        existing_active = RepackSession.objects.filter(
            personnel=personnel, status=RepackSession.STATUS_ACTIVE,
        ).first()
        if existing_active:
            return Response(
                {
                    'error': 'Ya hay una sesión activa para este operario.',
                    'session_id': existing_active.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = RepackSession.objects.create(
            personnel=personnel,
            distributor_center=dc,
            operational_date=request.data.get('operational_date') or timezone.localdate(),
            status=RepackSession.STATUS_ACTIVE,
            notes=request.data.get('notes', ''),
            started_by=request.user,
        )
        return Response(RepackSessionDetailSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Devuelve la sesión activa del operario actual (o null)."""
        personnel = _get_user_personnel(request.user)
        if not personnel:
            return Response(None)
        session = RepackSession.objects.filter(
            personnel=personnel, status=RepackSession.STATUS_ACTIVE,
        ).order_by('-started_at').first()
        if not session:
            return Response(None)
        return Response(RepackSessionDetailSerializer(session).data)

    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        """Cierra la sesión y emite el sample agregado del turno.

        Los samples por hora (`repack_boxes_per_hour`) ya se mantienen al día
        por los hooks de entry. Acá solo asegura el estado final + emite
        `repack_total_boxes_shift` y notifica a los suscriptores WS.
        """
        session = self.get_object()
        if session.status != RepackSession.STATUS_ACTIVE:
            return Response(
                {'error': f'La sesión está en estado "{session.get_status_display()}" — no se puede cerrar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            session.ended_at = timezone.now()
            session.status = RepackSession.STATUS_COMPLETED
            session.save(update_fields=['ended_at', 'status'])

        on_session_finished(session)

        return Response(RepackSessionDetailSerializer(session).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela la sesión sin emitir métricas."""
        session = self.get_object()
        if session.status != RepackSession.STATUS_ACTIVE:
            return Response(
                {'error': f'La sesión ya no está activa.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.ended_at = timezone.now()
        session.status = RepackSession.STATUS_CANCELLED
        session.notes = (session.notes + ' [cancelada]').strip()
        session.save(update_fields=['ended_at', 'status', 'notes'])
        return Response(RepackSessionDetailSerializer(session).data)


class RepackEntryViewSet(viewsets.ModelViewSet):
    """CRUD de entries de una sesión. La sesión debe estar ACTIVA.

    Permisos: solo el dueño de la sesión (`session.personnel.user`) o un
    admin pueden crear/editar/borrar entries. Cada cambio dispara
    recompute de los samples por hora + WS broadcast — el SIC se
    actualiza en vivo.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RepackEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session']

    def get_queryset(self):
        dc = _get_user_dc(self.request.user)
        qs = RepackEntry.objects.select_related('session', 'product')
        if dc:
            qs = qs.filter(session__distributor_center=dc)
        return qs

    def _check_owner_or_admin(self, session):
        user = self.request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied('Autenticación requerida.')
        if user.is_staff or user.is_superuser:
            return
        owner_user_id = getattr(session.personnel, 'user_id', None)
        if owner_user_id and owner_user_id == user.id:
            return
        raise PermissionDenied('Solo el operario dueño de la sesión o un admin pueden modificar entries.')

    def perform_create(self, serializer):
        session = serializer.validated_data.get('session')
        if not session:
            raise ValidationError({'session': 'Sesión requerida.'})
        if session.status != RepackSession.STATUS_ACTIVE:
            raise ValidationError({'session': 'La sesión no está activa.'})
        self._check_owner_or_admin(session)

        product = serializer.validated_data.get('product')
        box_count = serializer.validated_data.get('box_count', 0)

        if box_count == 0:
            raise ValidationError({'box_count': 'box_count no puede ser 0.'})

        # Producto opcional para los ajustes rápidos del botón +/- (caso
        # típico: el operario arregla la cuenta sin re-elegir SKU). Cuando
        # SÍ viene producto auto-rellenamos los descriptivos.
        if product:
            serializer.validated_data['material_code'] = product.sap_code or str(product.id)
            serializer.validated_data['product_name'] = product.name
        else:
            serializer.validated_data.setdefault('material_code', 'AJUSTE')
            serializer.validated_data.setdefault('product_name', 'Ajuste manual')

        instance = serializer.save()
        on_entry_changed(instance.session)

    def perform_update(self, serializer):
        instance = serializer.instance
        self._check_owner_or_admin(instance.session)
        if instance.session.status != RepackSession.STATUS_ACTIVE and not (
            self.request.user.is_staff or self.request.user.is_superuser
        ):
            raise ValidationError({'session': 'La sesión no está activa.'})
        if serializer.validated_data.get('box_count', instance.box_count) == 0:
            raise ValidationError({'box_count': 'box_count no puede ser 0.'})
        updated = serializer.save()
        on_entry_changed(updated.session)

    def perform_destroy(self, instance):
        self._check_owner_or_admin(instance.session)
        session = instance.session
        instance.delete()
        on_entry_changed(session)


