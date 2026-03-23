from django.db import models
from utils.BaseModel import BaseModel


class OvertimeDetail(BaseModel):
    """Detalle de horas extra"""

    class OvertimeType(models.TextChoices):
        REGULAR = 'REGULAR', 'Horas Extra Regulares'
        HOLIDAY = 'HOLIDAY', 'Horas en Feriado'
        WEEKEND = 'WEEKEND', 'Horas en Fin de Semana'
        NIGHT = 'NIGHT', 'Horas Nocturnas'
        DOUBLE = 'DOUBLE', 'Doble Turno'

    class OvertimeReason(models.TextChoices):
        PRODUCTION = 'PRODUCTION', 'Demanda de Producción'
        DEADLINE = 'DEADLINE', 'Cumplimiento de Plazo'
        COVERAGE = 'COVERAGE', 'Cobertura de Personal'
        EMERGENCY = 'EMERGENCY', 'Emergencia'
        SPECIAL_PROJECT = 'SPECIAL_PROJECT', 'Proyecto Especial'
        INVENTORY = 'INVENTORY', 'Inventario'
        MAINTENANCE = 'MAINTENANCE', 'Mantenimiento'
        OTHER = 'OTHER', 'Otro'

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='overtime_detail',
        verbose_name='Token'
    )
    overtime_type = models.CharField(
        max_length=20,
        choices=OvertimeType.choices,
        default=OvertimeType.REGULAR,
        verbose_name='Tipo de Hora Extra (legacy)'
    )
    overtime_type_model = models.ForeignKey(
        'tokens.OvertimeTypeModel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='overtime_details',
        verbose_name='Tipo de Hora Extra'
    )
    reason = models.CharField(
        max_length=20,
        choices=OvertimeReason.choices,
        verbose_name='Motivo (legacy)'
    )
    reason_model = models.ForeignKey(
        'tokens.OvertimeReasonModel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='overtime_details',
        verbose_name='Motivo'
    )
    reason_detail = models.TextField(
        blank=True,
        verbose_name='Detalle del Motivo'
    )
    # Fecha y horas
    overtime_date = models.DateField(
        verbose_name='Fecha de Horas Extra'
    )
    start_time = models.TimeField(
        verbose_name='Hora de Inicio'
    )
    end_time = models.TimeField(
        verbose_name='Hora de Fin'
    )
    # Horas calculadas
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Total de Horas'
    )
    # Multiplicador de pago
    pay_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.5,
        verbose_name='Multiplicador de Pago'
    )
    # Tarea específica
    assigned_task = models.TextField(
        blank=True,
        verbose_name='Tarea Asignada'
    )
    # Control de cumplimiento
    was_completed = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Completado'
    )
    actual_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora Real de Inicio'
    )
    actual_end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora Real de Fin'
    )
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Horas Reales'
    )
    completion_notes = models.TextField(
        blank=True,
        verbose_name='Notas de Cumplimiento'
    )

    class Meta:
        db_table = 'app_token_overtime_detail'
        verbose_name = 'Detalle de Horas Extra'
        verbose_name_plural = 'Detalles de Horas Extra'

    def __str__(self):
        return f"Horas extra - {self.token.display_number}"

    def save(self, *args, **kwargs):
        # Calcular total de horas automáticamente
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            if end < start:
                end += timedelta(days=1)
            diff = end - start
            self.total_hours = diff.seconds / 3600
        super().save(*args, **kwargs)

    @property
    def estimated_pay(self):
        """Calcula el pago estimado (si se conoce la tasa)"""
        return self.total_hours * self.pay_multiplier
