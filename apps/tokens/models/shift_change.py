from django.db import models
from utils.BaseModel import BaseModel


class ShiftChangeDetail(BaseModel):
    """Detalle de cambio de turno"""

    class ChangeReason(models.TextChoices):
        PERSONAL = 'PERSONAL', 'Motivo Personal'
        MEDICAL = 'MEDICAL', 'Cita Médica'
        EDUCATION = 'EDUCATION', 'Estudios'
        FAMILY = 'FAMILY', 'Asunto Familiar'
        TRANSPORT = 'TRANSPORT', 'Transporte'
        MUTUAL_AGREEMENT = 'MUTUAL_AGREEMENT', 'Acuerdo Mutuo'
        OPERATIONAL = 'OPERATIONAL', 'Necesidad Operativa'
        OTHER = 'OTHER', 'Otro'

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='shift_change_detail',
        verbose_name='Token'
    )
    reason = models.CharField(
        max_length=20,
        choices=ChangeReason.choices,
        verbose_name='Motivo del Cambio'
    )
    reason_detail = models.TextField(
        blank=True,
        verbose_name='Detalle del Motivo'
    )
    # Turno actual
    current_shift_name = models.CharField(
        max_length=100,
        verbose_name='Turno Actual'
    )
    current_shift_start = models.TimeField(
        verbose_name='Hora Inicio Turno Actual'
    )
    current_shift_end = models.TimeField(
        verbose_name='Hora Fin Turno Actual'
    )
    # Nuevo turno solicitado
    new_shift_name = models.CharField(
        max_length=100,
        verbose_name='Nuevo Turno'
    )
    new_shift_start = models.TimeField(
        verbose_name='Hora Inicio Nuevo Turno'
    )
    new_shift_end = models.TimeField(
        verbose_name='Hora Fin Nuevo Turno'
    )
    # Fecha(s) del cambio
    change_date = models.DateField(
        verbose_name='Fecha del Cambio'
    )
    is_permanent = models.BooleanField(
        default=False,
        verbose_name='Es Permanente'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Fin (si temporal)'
    )
    # Intercambio con otro personal (opcional)
    exchange_with = models.ForeignKey(
        'personnel.PersonnelProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shift_exchanges',
        verbose_name='Intercambio con'
    )
    exchange_confirmed = models.BooleanField(
        default=False,
        verbose_name='Intercambio Confirmado'
    )

    class Meta:
        db_table = 'app_token_shift_change_detail'
        verbose_name = 'Detalle de Cambio de Turno'
        verbose_name_plural = 'Detalles de Cambio de Turno'

    def __str__(self):
        return f"Cambio de turno - {self.token.display_number}"

    @property
    def is_exchange(self):
        """Indica si es un intercambio de turno con otro personal"""
        return self.exchange_with is not None
