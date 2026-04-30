"""
Endpoints del módulo TV.

- POST   /api/tv/sessions/                    (público)  crea pending, devuelve code
- GET    /api/tv/sessions/<code>/             (público)  estado (el QR page lo usa)
- POST   /api/tv/sessions/<code>/pair/        (auth)     pareo
- GET    /api/tv/sessions/mine/               (auth)     mis TVs paradas por DC
- POST   /api/tv/sessions/<pk>/revoke/        (auth)     admin revoca
- POST   /api/tv/sessions/<pk>/update_config/ (auth)     admin cambia dashboard/config en caliente
- GET    /api/tv/workstation/                 (TvToken)  datos del dashboard
- POST   /api/tv/heartbeat/                   (TvToken)  ping
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.maintenance.models.distributor_center import DistributorCenter, DCShiftModel
from apps.truck_cycle.models.core import PautaModel
from apps.truck_cycle.serializers import PautaListSerializer

from rest_framework_simplejwt.authentication import JWTAuthentication

from .auth import TvTokenAuthentication
from .models import TvSession
from .permissions import HasTvSession
from .serializers import (
    TvPairRequestSerializer,
    TvSessionAdminSerializer,
    TvSessionPairedSerializer,
    TvSessionPublicSerializer,
)


PENDING_TTL_MINUTES = 10


def _notify(code: str, kind: str, data: dict | None = None) -> None:
    """Dispara evento WS al grupo `tv_session_<code>`."""
    layer = get_channel_layer()
    if not layer:
        return
    async_to_sync(layer.group_send)(
        f'tv_session_{code}',
        {'type': kind, 'data': data or {}},
    )


class TvSessionViewSet(viewsets.GenericViewSet):
    """
    Viewset mixto: las acciones de admin (create/pair/revoke/etc) usan JWT; las
    de la TV (workstation/heartbeat) usan TvTokenAuthentication por el header
    X-TV-Token. Ambas auth classes se declaran juntas — cada una retorna None
    cuando no aplica, y DRF prueba la siguiente.
    """

    queryset = TvSession.objects.all()
    lookup_field = 'code'
    lookup_value_regex = r'[A-Z0-9\-]{3,16}'
    # IMPORTANTE: se resuelven en orden. TvTokenAuthentication devuelve None si
    # no hay header X-TV-Token, así que las requests con JWT pasan a la siguiente.
    authentication_classes = [TvTokenAuthentication, JWTAuthentication]

    def get_permissions(self):
        if self.action in ('create', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action in ('workstation', 'heartbeat'):
            return [HasTvSession()]
        return [permissions.IsAuthenticated()]

    def create(self, request):
        """La TV crea una sesión PENDING."""
        session = TvSession.objects.create(
            expires_at=timezone.now() + timezone.timedelta(minutes=PENDING_TTL_MINUTES),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
            ip_address=_client_ip(request),
        )
        return Response(TvSessionPublicSerializer(session).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, code=None):
        """Estado público (usado por la página del QR / polling fallback)."""
        session = self._get_by_code(code)
        if not session:
            return Response({'error': 'No existe.'}, status=status.HTTP_404_NOT_FOUND)
        session.mark_expired_if_needed()
        return Response(TvSessionPublicSerializer(session).data)

    # ---------- POST /api/tv/sessions/<code>/pair/ ----------
    @action(detail=True, methods=['post'])
    def pair(self, request, code=None):
        session = self._get_by_code(code)
        if not session:
            return Response({'error': 'Código no encontrado.'}, status=404)
        session.mark_expired_if_needed()
        if session.status != 'PENDING':
            return Response(
                {'error': f'La sesión está en estado "{session.get_status_display()}".'},
                status=400,
            )

        serializer = TvPairRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            dc = DistributorCenter.objects.get(pk=data['distributor_center'])
        except DistributorCenter.DoesNotExist:
            return Response({'error': 'Centro de distribución no existe.'}, status=400)

        session.pair(
            user=request.user,
            dc=dc,
            dashboard=data['dashboard'],
            config=data.get('config') or {},
            label=data.get('label') or '',
            ttl_days=data.get('ttl_days') or 7,
        )

        # Notifica a la TV por WS con el token + config.
        _notify(session.code, 'session.paired', {
            'access_token': session.access_token,
            'dashboard': session.dashboard,
            'distributor_center': session.distributor_center_id,
            'distributor_center_name': dc.name,
            'expires_at': session.expires_at.isoformat(),
            'config': session.config,
            'label': session.label,
        })

        return Response(TvSessionPairedSerializer(session).data)

    # ---------- GET /api/tv/sessions/mine/ ----------
    @action(detail=False, methods=['get'])
    def mine(self, request):
        """
        Lista las TVs del CD del usuario autenticado (o cualquiera si es admin).

        Params opcionales:
            distributor_center=<id>  — admin filtra por CD específico
            include_inactive=1       — incluye revocadas/expiradas (para historial)
        """
        qs = TvSession.objects.all()

        dc_param = request.query_params.get('distributor_center')
        if dc_param:
            if not (request.user.is_superuser or request.user.is_staff):
                # Usuarios normales solo pueden listar TVs de su propio CD.
                if int(dc_param) != (request.user.centro_distribucion_id or -1):
                    return Response([])
            qs = qs.filter(distributor_center_id=dc_param)
        elif not (request.user.is_superuser or request.user.is_staff):
            if not request.user.centro_distribucion_id:
                return Response([])
            qs = qs.filter(distributor_center_id=request.user.centro_distribucion_id)

        include_inactive = request.query_params.get('include_inactive') in ('1', 'true', 'True')
        if not include_inactive:
            qs = qs.filter(status='PAIRED', expires_at__gt=timezone.now())

        qs = qs.order_by('-paired_at', '-created_at')
        return Response(TvSessionAdminSerializer(qs, many=True).data)

    # ---------- POST /api/tv/sessions/<pk>/revoke/ ----------
    @action(detail=True, methods=['post'])
    def revoke(self, request, code=None):
        session = self._get_by_code(code)
        if not session:
            return Response({'error': 'No existe.'}, status=404)
        session.revoke()
        _notify(session.code, 'session.revoked')
        return Response({'status': session.status})

    # ---------- POST /api/tv/sessions/<code>/update_config/ ----------
    @action(detail=True, methods=['post'], url_path='update_config')
    def update_config(self, request, code=None):
        """Cambiar dashboard o config sin reparear."""
        session = self._get_by_code(code)
        if not session or session.status != 'PAIRED':
            return Response({'error': 'La sesión no está pareada.'}, status=400)

        dashboard = request.data.get('dashboard')
        config = request.data.get('config')
        label = request.data.get('label')
        updated_fields = []
        if dashboard and dashboard in dict(TvSession.DASHBOARD_CHOICES):
            session.dashboard = dashboard
            updated_fields.append('dashboard')
        if config is not None:
            session.config = config
            updated_fields.append('config')
        if label is not None:
            session.label = label
            updated_fields.append('label')
        if updated_fields:
            session.save(update_fields=updated_fields)
            _notify(session.code, 'session.updated', {
                'dashboard': session.dashboard,
                'config': session.config,
                'label': session.label,
            })
        return Response(TvSessionAdminSerializer(session).data)

    # ---------- TvToken-authed ----------
    @action(detail=False, methods=['post'])
    def heartbeat(self, request):
        # TvTokenAuthentication ya actualizó last_seen_at.
        return Response({'ok': True, 'server_time': timezone.now().isoformat()})

    @action(detail=False, methods=['get'])
    def workstation(self, request):
        """Datos del dashboard Workstation — scoped al CD de la sesión.

        Incluye `workstation_config` con riesgos/prohibiciones/triggers/planes/
        documentos resueltos por (CD, role-derivado-del-dashboard).
        """
        session: TvSession = request.tv_session
        dc_id = session.distributor_center_id

        operational_date = request.query_params.get('operational_date') or timezone.localdate().isoformat()
        qs = PautaModel.objects.filter(operational_date=operational_date)
        if dc_id:
            qs = qs.filter(distributor_center_id=dc_id)

        grouped = {}
        for choice_value, choice_label in PautaModel.STATUS_CHOICES:
            pautas = qs.filter(status=choice_value)
            grouped[choice_value] = {
                'label': choice_label,
                'count': pautas.count(),
                'pautas': PautaListSerializer(pautas, many=True).data,
            }

        reload_queue = list(qs.filter(status='IN_RELOAD_QUEUE').order_by('created_at'))
        shift_info = _shift_info(dc_id) if dc_id else {'current': None, 'today': [], 'day_code': None}

        # Config del Workstation (riesgos, prohibiciones, planes, SOPs/OPLs).
        # Importación local para evitar ciclo de imports en el setup de la app.
        from apps.workstation.views import get_workstation_for_tv
        from apps.workstation.serializers import WorkstationSerializer
        ws = get_workstation_for_tv(session.dashboard, dc_id)
        workstation_config = WorkstationSerializer(ws).data if ws else None

        return Response({
            'operational_date': operational_date,
            'workstation': grouped,
            'reload_queue': PautaListSerializer(reload_queue, many=True).data,
            'dashboard': session.dashboard,
            'label': session.label,
            'distributor_center': dc_id,
            'current_shift': shift_info['current'],
            'shifts_today': shift_info['today'],
            'day_code': shift_info['day_code'],
            'workstation_config': workstation_config,
        })

    # ---------- helpers ----------
    def _get_by_code(self, code):
        try:
            return TvSession.objects.select_related('distributor_center').get(code=code)
        except TvSession.DoesNotExist:
            return None


def _client_ip(request) -> str | None:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


_DAY_CODES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']


def _shift_is_active(shift: DCShiftModel, day_today: str, day_prev: str, day_next: str, now_time) -> bool:
    """
    Determina si un turno está activo ahora — soporta ambas convenciones para
    turnos nocturnos: `day_of_week` puede ser el día en que inicia o el día en
    que termina. Aceptamos ambos para cubrir el caso del usuario donde TC
    "Lunes 20:30-06:00" significa el turno que termina lunes 06:00.
    """
    start, end = shift.start_time, shift.end_time
    if start <= end:
        return shift.day_of_week == day_today and start <= now_time <= end

    # Overnight (cruza medianoche).
    if shift.day_of_week == day_today:
        # Estamos en ese día — puede ser primera mitad (≥ start) o segunda (≤ end).
        return now_time >= start or now_time <= end
    if shift.day_of_week == day_prev:
        # Turno configurado como "ayer" rodando hacia hoy.
        return now_time <= end
    if shift.day_of_week == day_next:
        # Turno configurado como "mañana" que ya empezó esta noche.
        return now_time >= start
    return False


def _shift_info(dc_id: int) -> dict:
    """Turno activo + lista de turnos de hoy + código de día."""
    now = timezone.localtime()
    day_idx = now.weekday()
    day_today = _DAY_CODES[day_idx]
    day_prev  = _DAY_CODES[(day_idx - 1) % 7]
    day_next  = _DAY_CODES[(day_idx + 1) % 7]
    now_time = now.time()

    # Prioridad: turnos configurados como HOY (cubre la convención end-day);
    # luego AYER (cubre la convención start-day con overnight rodando);
    # luego MAÑANA (cubre overnight que arranca esta noche).
    current = None
    for day_to_try in (day_today, day_prev, day_next):
        shifts = DCShiftModel.objects.filter(
            distributor_center_id=dc_id, is_active=True, day_of_week=day_to_try,
        ).order_by('start_time')
        for s in shifts:
            if _shift_is_active(s, day_today, day_prev, day_next, now_time):
                current = _shift_payload(s)
                break
        if current:
            break

    today_shifts = DCShiftModel.objects.filter(
        distributor_center_id=dc_id, is_active=True, day_of_week=day_today,
    ).order_by('start_time')

    return {
        'current': current,
        'today': [_shift_payload(s) for s in today_shifts],
        'day_code': day_today,
    }


def _shift_payload(shift: DCShiftModel) -> dict:
    return {
        'name': shift.shift_name,
        'day_of_week': shift.get_day_of_week_display(),
        'start_time': shift.start_time.strftime('%H:%M'),
        'end_time': shift.end_time.strftime('%H:%M'),
    }
