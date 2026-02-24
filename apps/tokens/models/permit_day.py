from django.db import models
from utils.BaseModel import BaseModel


class PermitDayDetail(BaseModel):
    """Detalle del permiso por día(s)"""

    class DateSelectionType(models.TextChoices):
        SINGLE = 'SINGLE', 'Día Único'
        RANGE = 'RANGE', 'Rango de Días'
        MULTIPLE = 'MULTIPLE', 'Días Múltiples'

    class PermitReason(models.TextChoices):
        MEDICAL = 'MEDICAL', 'Cita Médica'
        FAMILY = 'FAMILY', 'Asunto Familiar'
        PERSONAL = 'PERSONAL', 'Asunto Personal'
        LEGAL = 'LEGAL', 'Asunto Legal/Trámite'
        EDUCATION = 'EDUCATION', 'Educación/Capacitación'
        BEREAVEMENT = 'BEREAVEMENT', 'Duelo'
        WEDDING = 'WEDDING', 'Matrimonio'
        PATERNITY = 'PATERNITY', 'Paternidad'
        MATERNITY = 'MATERNITY', 'Maternidad'
        VACATION = 'VACATION', 'Vacaciones'
        OTHER = 'OTHER', 'Otro'

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='permit_day_detail',
        verbose_name='Token'
    )
    date_selection_type = models.CharField(
        max_length=20,
        choices=DateSelectionType.choices,
        default=DateSelectionType.SINGLE,
        verbose_name='Tipo de Selección'
    )
    reason = models.CharField(
        max_length=20,
        choices=PermitReason.choices,
        verbose_name='Motivo'
    )
    reason_detail = models.TextField(
        blank=True,
        verbose_name='Detalle del Motivo'
    )
    with_pay = models.BooleanField(
        default=True,
        verbose_name='Con Goce de Sueldo'
    )
    # Para rango de fechas
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Inicio'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Fin'
    )

    class Meta:
        db_table = 'app_token_permit_day_detail'
        verbose_name = 'Detalle de Permiso por Día'
        verbose_name_plural = 'Detalles de Permiso por Día'

    def __str__(self):
        return f"Permiso por día - {self.token.display_number}"

    @property
    def total_days(self):
        """Calcula el total de días del permiso"""
        if self.date_selection_type == self.DateSelectionType.MULTIPLE:
            return self.selected_dates.count()
        elif self.date_selection_type == self.DateSelectionType.RANGE and self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        elif self.date_selection_type == self.DateSelectionType.SINGLE:
            return 1
        return 0


class PermitDayDate(BaseModel):
    """Fecha individual seleccionada para permiso por días múltiples"""

    permit_day = models.ForeignKey(
        PermitDayDetail,
        on_delete=models.CASCADE,
        related_name='selected_dates',
        verbose_name='Permiso por Día'
    )
    date = models.DateField(
        verbose_name='Fecha'
    )
    notes = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Notas'
    )

    class Meta:
        db_table = 'app_token_permit_day_date'
        verbose_name = 'Fecha de Permiso'
        verbose_name_plural = 'Fechas de Permiso'
        ordering = ['date']
        unique_together = ['permit_day', 'date']

    def __str__(self):
        return str(self.date)
