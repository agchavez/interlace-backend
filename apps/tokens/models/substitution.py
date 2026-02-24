from django.db import models
from utils.BaseModel import BaseModel


class SubstitutionDetail(BaseModel):
    """Detalle de sustitución de personal"""

    class SubstitutionReason(models.TextChoices):
        ABSENCE = 'ABSENCE', 'Ausencia'
        VACATION = 'VACATION', 'Vacaciones'
        MEDICAL_LEAVE = 'MEDICAL_LEAVE', 'Licencia Médica'
        TRAINING = 'TRAINING', 'Capacitación'
        PROMOTION = 'PROMOTION', 'Promoción Temporal'
        EMERGENCY = 'EMERGENCY', 'Emergencia'
        OTHER = 'OTHER', 'Otro'

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='substitution_detail',
        verbose_name='Token'
    )
    # Personal que será sustituido (el beneficiario del token es quien sustituye)
    substituted_personnel = models.ForeignKey(
        'personnel.PersonnelProfile',
        on_delete=models.PROTECT,
        related_name='substitutions_received',
        verbose_name='Personal Sustituido'
    )
    reason = models.CharField(
        max_length=20,
        choices=SubstitutionReason.choices,
        verbose_name='Motivo'
    )
    reason_detail = models.TextField(
        blank=True,
        verbose_name='Detalle del Motivo'
    )
    # Funciones que asumirá
    assumed_functions = models.TextField(
        verbose_name='Funciones a Asumir'
    )
    # Fechas
    start_date = models.DateField(
        verbose_name='Fecha Inicio'
    )
    end_date = models.DateField(
        verbose_name='Fecha Fin'
    )
    # Horario específico (opcional)
    specific_schedule = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Horario Específico'
    )
    # Compensación adicional (si aplica)
    additional_compensation = models.BooleanField(
        default=False,
        verbose_name='Compensación Adicional'
    )
    compensation_notes = models.TextField(
        blank=True,
        verbose_name='Notas de Compensación'
    )

    class Meta:
        db_table = 'app_token_substitution_detail'
        verbose_name = 'Detalle de Sustitución'
        verbose_name_plural = 'Detalles de Sustitución'

    def __str__(self):
        return f"Sustitución - {self.token.display_number}"

    @property
    def total_days(self):
        """Calcula el total de días de sustitución"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
