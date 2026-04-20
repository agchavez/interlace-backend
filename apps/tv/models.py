"""
Modelos del módulo TV — dashboards en pantallas grandes con pareo por QR.

Flujo: una TV crea una TvSession en estado PENDING, muestra el code en un QR.
Un usuario autenticado escanea, abre la URL de pareo, elige CD + dashboard,
confirma. La sesión pasa a PAIRED y se genera un access_token opaco que la TV
usa para leer solo-lectura los datos del dashboard configurado.
"""
import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone


def _gen_code() -> str:
    """Genera un code corto estilo 'A3F9-K2Q1' (evita caracteres confusos)."""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # sin 0/O/1/I/L
    first = ''.join(secrets.choice(alphabet) for _ in range(4))
    second = ''.join(secrets.choice(alphabet) for _ in range(4))
    return f'{first}-{second}'


def _gen_token() -> str:
    """Token opaco URL-safe — se guarda plano para poder revocar desde DB."""
    return secrets.token_urlsafe(32)


class TvSession(models.Model):
    STATUS_CHOICES = [
        ('PENDING',  'Pendiente'),
        ('PAIRED',   'Pareada'),
        ('EXPIRED',  'Expirada'),
        ('REVOKED',  'Revocada'),
    ]
    DASHBOARD_CHOICES = [
        ('WORKSTATION',         'Workstation (estaciones de trabajo)'),
        ('WORKSTATION_PICKING', 'Estación de trabajo del operador · Picking'),
    ]

    code = models.CharField('Código', max_length=9, unique=True, db_index=True, default=_gen_code)
    access_token = models.CharField('Token', max_length=64, unique=True, null=True, blank=True, db_index=True)
    status = models.CharField('Estado', max_length=10, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField('Expira en')
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    last_seen_at = models.DateTimeField('Último heartbeat', null=True, blank=True)

    # Configuración del dashboard (llenada al parear)
    paired_at = models.DateTimeField('Pareada en', null=True, blank=True)
    paired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tv_sessions_paired',
        verbose_name='Pareada por',
    )
    distributor_center = models.ForeignKey(
        'maintenance.DistributorCenter',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='tv_sessions',
        verbose_name='Centro de distribución',
    )
    dashboard = models.CharField(
        'Dashboard', max_length=20, choices=DASHBOARD_CHOICES,
        default='WORKSTATION',
    )
    config = models.JSONField('Configuración', default=dict, blank=True)

    # Etiqueta humana opcional ("TV Recepción", "TV Muelle 3") y meta debug.
    label = models.CharField('Etiqueta', max_length=80, blank=True, default='')
    user_agent = models.CharField('User-Agent', max_length=300, blank=True, default='')
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)

    class Meta:
        db_table = 'tv_session'
        verbose_name = 'Sesión de TV'
        verbose_name_plural = 'Sesiones de TV'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f'{self.code} [{self.status}]'

    # ---- Helpers de estado ----
    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    def is_valid_for_use(self) -> bool:
        return self.status == 'PAIRED' and not self.is_expired

    def mark_expired_if_needed(self) -> None:
        if self.status == 'PENDING' and self.is_expired:
            self.status = 'EXPIRED'
            self.save(update_fields=['status'])

    def pair(self, *, user, dc, dashboard='WORKSTATION', config=None, label='', ttl_days: int = 7):
        """Marca la sesión como pareada y genera el access_token."""
        self.access_token = _gen_token()
        self.status = 'PAIRED'
        self.paired_at = timezone.now()
        self.paired_by = user
        self.distributor_center = dc
        self.dashboard = dashboard
        self.config = config or {}
        self.label = label or self.label
        self.expires_at = timezone.now() + timezone.timedelta(days=ttl_days)
        self.save()

    def revoke(self) -> None:
        self.status = 'REVOKED'
        self.access_token = None
        self.save(update_fields=['status', 'access_token'])
