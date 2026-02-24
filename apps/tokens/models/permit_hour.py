from django.db import models


class PermitHourDetail(models.Model):
    """
    Detalle específico para tokens de tipo PERMIT_HOUR (Permiso por Hora).
    """

    class PermitReason(models.TextChoices):
        MEDICAL = 'MEDICAL', 'Cita Médica'
        PERSONAL = 'PERSONAL', 'Asunto Personal'
        BANK = 'BANK', 'Trámite Bancario'
        GOVERNMENT = 'GOVERNMENT', 'Trámite Gubernamental'
        FAMILY = 'FAMILY', 'Asunto Familiar'
        EDUCATION = 'EDUCATION', 'Asunto Educativo'
        OTHER = 'OTHER', 'Otro'

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='permit_hour_detail',
        verbose_name='Token'
    )

    # Motivo del permiso
    reason_type = models.CharField(
        max_length=20,
        choices=PermitReason.choices,
        verbose_name='Tipo de Motivo'
    )
    reason_description = models.TextField(
        blank=True,
        verbose_name='Descripción del Motivo'
    )

    # Horas solicitadas
    hours_requested = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='Horas Solicitadas'
    )

    # Hora de salida y retorno esperado
    exit_time = models.TimeField(
        verbose_name='Hora de Salida'
    )
    expected_return_time = models.TimeField(
        verbose_name='Hora de Retorno Esperada'
    )

    # Registro real (llenado por Seguridad)
    actual_exit_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Salida Real'
    )
    actual_return_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Retorno Real'
    )

    # Con o sin goce de sueldo
    with_pay = models.BooleanField(
        default=True,
        verbose_name='Con Goce de Sueldo'
    )

    class Meta:
        db_table = 'app_token_permit_hour_detail'
        verbose_name = 'Detalle Permiso por Hora'
        verbose_name_plural = 'Detalles Permiso por Hora'

    def __str__(self):
        return f"Permiso Hora: {self.token.display_number}"

    @property
    def actual_hours_used(self):
        """Calcula las horas realmente utilizadas"""
        if self.actual_exit_time and self.actual_return_time:
            from datetime import datetime, timedelta
            exit_dt = datetime.combine(datetime.today(), self.actual_exit_time)
            return_dt = datetime.combine(datetime.today(), self.actual_return_time)

            # Manejar caso donde retorno es al día siguiente
            if return_dt < exit_dt:
                return_dt += timedelta(days=1)

            diff = return_dt - exit_dt
            return round(diff.total_seconds() / 3600, 2)
        return None
