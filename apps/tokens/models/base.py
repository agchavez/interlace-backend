import uuid
from django.db import models
from django.utils import timezone
from utils.BaseModel import BaseModel


class TokenRequest(BaseModel):
    """
    Modelo base para todos los tipos de tokens.
    Cada tipo de token tiene un modelo de detalle asociado (OneToOne).
    """

    class TokenType(models.TextChoices):
        PERMIT_HOUR = 'PERMIT_HOUR', 'Permiso por Hora'
        PERMIT_DAY = 'PERMIT_DAY', 'Permiso por Día'
        EXIT_PASS = 'EXIT_PASS', 'Pase de Salida'
        SUBSTITUTION = 'SUBSTITUTION', 'Sustitución'
        RATE_CHANGE = 'RATE_CHANGE', 'Cambio de Tasa'
        OVERTIME = 'OVERTIME', 'Horas Extra'
        SHIFT_CHANGE = 'SHIFT_CHANGE', 'Cambio de Turno'
        UNIFORM_DELIVERY = 'UNIFORM_DELIVERY', 'Entrega de Uniforme'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        PENDING_L1 = 'PENDING_L1', 'Pendiente Nivel 1'
        PENDING_L2 = 'PENDING_L2', 'Pendiente Nivel 2'
        PENDING_L3 = 'PENDING_L3', 'Pendiente Nivel 3'
        APPROVED = 'APPROVED', 'Aprobado'
        USED = 'USED', 'Utilizado'
        EXPIRED = 'EXPIRED', 'Expirado'
        CANCELLED = 'CANCELLED', 'Cancelado'
        REJECTED = 'REJECTED', 'Rechazado'

    # Identificadores únicos
    token_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Código UUID'
    )
    display_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name='Número de Token'
    )

    # Tipo y estado
    token_type = models.CharField(
        max_length=20,
        choices=TokenType.choices,
        verbose_name='Tipo de Token'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Estado'
    )

    # Personal involucrado
    personnel = models.ForeignKey(
        'personnel.PersonnelProfile',
        on_delete=models.PROTECT,
        related_name='tokens_received',
        verbose_name='Beneficiario'
    )
    requested_by = models.ForeignKey(
        'user.UserModel',
        on_delete=models.PROTECT,
        related_name='tokens_requested',
        verbose_name='Solicitado por'
    )

    # Ubicación
    distributor_center = models.ForeignKey(
        'maintenance.DistributorCenter',
        on_delete=models.PROTECT,
        related_name='tokens',
        verbose_name='Centro de Distribución'
    )

    # Código QR
    qr_code_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL del QR'
    )

    # Configuración de aprobaciones requeridas
    requires_level_1 = models.BooleanField(
        default=True,
        verbose_name='Requiere Nivel 1'
    )
    requires_level_2 = models.BooleanField(
        default=True,
        verbose_name='Requiere Nivel 2'
    )
    requires_level_3 = models.BooleanField(
        default=False,
        verbose_name='Requiere Nivel 3'
    )

    # Aprobación Nivel 1 (Supervisor)
    approved_level_1_by = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tokens_approved_l1',
        verbose_name='Aprobado L1 por'
    )
    approved_level_1_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Aprobación L1'
    )
    approved_level_1_notes = models.TextField(
        blank=True,
        verbose_name='Notas Aprobación L1'
    )
    approved_level_1_signature = models.ImageField(
        upload_to='tokens/approvals/signatures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Firma Aprobación L1'
    )
    approved_level_1_photo = models.ImageField(
        upload_to='tokens/approvals/photos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto Aprobación L1'
    )

    # Aprobación Nivel 2 (Jefe de Área)
    approved_level_2_by = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tokens_approved_l2',
        verbose_name='Aprobado L2 por'
    )
    approved_level_2_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Aprobación L2'
    )
    approved_level_2_notes = models.TextField(
        blank=True,
        verbose_name='Notas Aprobación L2'
    )
    approved_level_2_signature = models.ImageField(
        upload_to='tokens/approvals/signatures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Firma Aprobación L2'
    )
    approved_level_2_photo = models.ImageField(
        upload_to='tokens/approvals/photos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto Aprobación L2'
    )

    # Aprobación Nivel 3 (Gerente CD)
    approved_level_3_by = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tokens_approved_l3',
        verbose_name='Aprobado L3 por'
    )
    approved_level_3_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Aprobación L3'
    )
    approved_level_3_notes = models.TextField(
        blank=True,
        verbose_name='Notas Aprobación L3'
    )
    approved_level_3_signature = models.ImageField(
        upload_to='tokens/approvals/signatures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Firma Aprobación L3'
    )
    approved_level_3_photo = models.ImageField(
        upload_to='tokens/approvals/photos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto Aprobación L3'
    )

    # Rechazo
    rejected_by = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tokens_rejected',
        verbose_name='Rechazado por'
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Rechazo'
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de Rechazo'
    )

    # Validación (por Seguridad)
    validated_by = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tokens_validated',
        verbose_name='Validado por'
    )
    validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Validación'
    )
    validation_signature = models.ImageField(
        upload_to='tokens/validations/signatures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Firma de Validación'
    )
    validation_photo = models.ImageField(
        upload_to='tokens/validations/photos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto de Validación'
    )
    validation_notes = models.TextField(
        blank=True,
        verbose_name='Notas de Validación'
    )

    # Período de vigencia
    valid_from = models.DateTimeField(
        verbose_name='Válido Desde'
    )
    valid_until = models.DateTimeField(
        verbose_name='Válido Hasta'
    )

    # Notas
    requester_notes = models.TextField(
        blank=True,
        verbose_name='Notas del Solicitante'
    )
    internal_notes = models.TextField(
        blank=True,
        verbose_name='Notas Internas'
    )

    class Meta:
        db_table = 'app_token_request'
        verbose_name = 'Solicitud de Token'
        verbose_name_plural = 'Solicitudes de Token'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_code']),
            models.Index(fields=['display_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['personnel', 'created_at']),
            models.Index(fields=['distributor_center', 'status']),
            models.Index(fields=['token_type', 'status']),
        ]

    def __str__(self):
        return f"{self.display_number} - {self.get_token_type_display()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.display_number:
            self.display_number = self._generate_display_number()
        super().save(*args, **kwargs)

    def _generate_display_number(self):
        """Genera número de display: TK-2026-000001"""
        year = timezone.now().year
        prefix = f"TK-{year}-"
        last_token = TokenRequest.objects.filter(
            display_number__startswith=prefix
        ).order_by('-display_number').first()

        if last_token:
            last_num = int(last_token.display_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:06d}"

    @property
    def is_valid(self):
        """Verifica si el token está dentro del período de vigencia"""
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    @property
    def is_approved(self):
        """Verifica si el token está aprobado"""
        return self.status == self.Status.APPROVED

    @property
    def can_be_used(self):
        """Verifica si el token puede ser utilizado"""
        return self.is_approved and self.is_valid

    @property
    def approval_progress(self):
        """Retorna el progreso de aprobación como porcentaje"""
        total_levels = sum([
            self.requires_level_1,
            self.requires_level_2,
            self.requires_level_3
        ])
        if total_levels == 0:
            return 100

        approved_levels = sum([
            bool(self.approved_level_1_at) if self.requires_level_1 else False,
            bool(self.approved_level_2_at) if self.requires_level_2 else False,
            bool(self.approved_level_3_at) if self.requires_level_3 else False,
        ])

        return int((approved_levels / total_levels) * 100)

    def get_current_approval_level(self):
        """Retorna el nivel de aprobación actual pendiente"""
        if self.status == self.Status.REJECTED:
            return None
        if self.status == self.Status.APPROVED:
            return None

        if self.requires_level_1 and not self.approved_level_1_at:
            return 1
        if self.requires_level_2 and not self.approved_level_2_at:
            return 2
        if self.requires_level_3 and not self.approved_level_3_at:
            return 3

        return None

    def can_user_approve(self, personnel, level):
        """Verifica si el personal puede aprobar el token en el nivel especificado"""
        if self.status == self.Status.REJECTED:
            return False

        # No puede aprobar su propio token
        if self.personnel == personnel:
            return False

        # Verificar si es el nivel actual pendiente
        current_level = self.get_current_approval_level()
        if current_level != level:
            return False

        # Verificar permisos según nivel
        if level == 1:
            return personnel.can_approve_tokens_level_1()
        elif level == 2:
            return personnel.can_approve_tokens_level_2()
        elif level == 3:
            return personnel.can_approve_tokens_level_3()

        return False

    def approve_level_1(self, personnel, notes='', signature=None, photo=None):
        """Aprobar nivel 1"""
        if not self.can_user_approve(personnel, 1):
            raise ValueError("No tiene permiso para aprobar este token en nivel 1")

        self.approved_level_1_by = personnel
        self.approved_level_1_at = timezone.now()
        self.approved_level_1_notes = notes
        if signature:
            self.approved_level_1_signature = signature
        if photo:
            self.approved_level_1_photo = photo

        # Determinar siguiente estado
        if self.requires_level_2:
            self.status = self.Status.PENDING_L2
        elif self.requires_level_3:
            self.status = self.Status.PENDING_L3
        else:
            self.status = self.Status.APPROVED

        self.save()

    def approve_level_2(self, personnel, notes='', signature=None, photo=None):
        """Aprobar nivel 2"""
        if not self.can_user_approve(personnel, 2):
            raise ValueError("No tiene permiso para aprobar este token en nivel 2")

        self.approved_level_2_by = personnel
        self.approved_level_2_at = timezone.now()
        self.approved_level_2_notes = notes
        if signature:
            self.approved_level_2_signature = signature
        if photo:
            self.approved_level_2_photo = photo

        # Determinar siguiente estado
        if self.requires_level_3:
            self.status = self.Status.PENDING_L3
        else:
            self.status = self.Status.APPROVED

        self.save()

    def approve_level_3(self, personnel, notes='', signature=None, photo=None):
        """Aprobar nivel 3"""
        if not self.can_user_approve(personnel, 3):
            raise ValueError("No tiene permiso para aprobar este token en nivel 3")

        self.approved_level_3_by = personnel
        self.approved_level_3_at = timezone.now()
        self.approved_level_3_notes = notes
        if signature:
            self.approved_level_3_signature = signature
        if photo:
            self.approved_level_3_photo = photo
        self.status = self.Status.APPROVED
        self.save()

    def reject(self, personnel, reason):
        """Rechazar el token"""
        if self.status in [self.Status.APPROVED, self.Status.USED, self.Status.EXPIRED]:
            raise ValueError("No se puede rechazar un token en este estado")

        self.rejected_by = personnel
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.status = self.Status.REJECTED
        self.save()

    def mark_as_used(self, validated_by, signature=None, photo=None, notes=''):
        """Marcar el token como utilizado (validado por Seguridad)"""
        if not self.can_be_used:
            raise ValueError("El token no puede ser utilizado")

        self.validated_by = validated_by
        self.validated_at = timezone.now()
        self.validation_notes = notes
        if signature:
            self.validation_signature = signature
        if photo:
            self.validation_photo = photo
        self.status = self.Status.USED
        self.save()

    def cancel(self):
        """Cancelar el token"""
        if self.status in [self.Status.USED, self.Status.EXPIRED]:
            raise ValueError("No se puede cancelar un token en este estado")

        self.status = self.Status.CANCELLED
        self.save()

    def mark_as_expired(self):
        """Marcar el token como expirado"""
        if self.status == self.Status.APPROVED and not self.is_valid:
            self.status = self.Status.EXPIRED
            self.save()
