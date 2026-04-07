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
        """Calcula el pago estimado sumando todos los segmentos o usando el multiplicador base"""
        if self.segments.exists():
            return sum(s.estimated_pay for s in self.segments.all())
        return self.total_hours * self.pay_multiplier

    @property
    def is_variable_rate(self):
        """Indica si tiene múltiples tramos de pago"""
        return self.segments.count() > 1

    def recalculate_totals(self):
        """Recalcular total_hours desde los segmentos si existen"""
        segments = self.segments.all()
        if segments.exists():
            self.total_hours = sum(s.hours for s in segments)
            self.save(update_fields=['total_hours'])


class OvertimeSegment(BaseModel):
    """Segmento de horas extra con multiplicador específico.
    Permite tener múltiples tramos con diferente % de pago en un solo token.
    Ejemplo: 6PM-7PM al 240%, 7PM-6AM al 300%
    """

    overtime_detail = models.ForeignKey(
        OvertimeDetail,
        on_delete=models.CASCADE,
        related_name='segments',
        verbose_name='Detalle de Hora Extra'
    )
    start_time = models.TimeField(
        verbose_name='Hora de Inicio'
    )
    end_time = models.TimeField(
        verbose_name='Hora de Fin'
    )
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Horas del Segmento'
    )
    pay_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.5,
        verbose_name='Multiplicador de Pago (%)',
        help_text='Ej: 2.40 para 240%, 3.00 para 300%'
    )
    overtime_type_model = models.ForeignKey(
        'tokens.OvertimeTypeModel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='overtime_segments',
        verbose_name='Tipo de Hora Extra'
    )
    sequence = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )

    class Meta:
        db_table = 'app_token_overtime_segment'
        verbose_name = 'Segmento de Hora Extra'
        verbose_name_plural = 'Segmentos de Hora Extra'
        ordering = ['sequence', 'start_time']

    def __str__(self):
        return f"{self.start_time}-{self.end_time} x{self.pay_multiplier}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            if end < start:
                end += timedelta(days=1)
            self.hours = (end - start).seconds / 3600
        super().save(*args, **kwargs)

    @property
    def estimated_pay(self):
        return self.hours * self.pay_multiplier
