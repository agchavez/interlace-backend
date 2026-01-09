from django.db import models
from utils.BaseModel import BaseModel


class RateChangeDetail(BaseModel):
    """Detalle de cambio de tasa temporal"""

    class ChangeReason(models.TextChoices):
        TEMPORARY_ASSIGNMENT = 'TEMPORARY_ASSIGNMENT', 'Asignación Temporal'
        SPECIAL_PROJECT = 'SPECIAL_PROJECT', 'Proyecto Especial'
        ADDITIONAL_RESPONSIBILITY = 'ADDITIONAL_RESPONSIBILITY', 'Responsabilidad Adicional'
        COVERAGE = 'COVERAGE', 'Cobertura de Puesto'
        INCENTIVE = 'INCENTIVE', 'Incentivo'
        OTHER = 'OTHER', 'Otro'

    token = models.OneToOneField(
        'tokens.TokenRequest',
        on_delete=models.CASCADE,
        related_name='rate_change_detail',
        verbose_name='Token'
    )
    reason = models.CharField(
        max_length=30,
        choices=ChangeReason.choices,
        verbose_name='Motivo del Cambio'
    )
    reason_detail = models.TextField(
        blank=True,
        verbose_name='Detalle del Motivo'
    )
    # Tasa actual y nueva
    current_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Tasa Actual'
    )
    new_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Nueva Tasa'
    )
    rate_type = models.CharField(
        max_length=50,
        default='Horaria',
        verbose_name='Tipo de Tasa'
    )
    # Período de aplicación
    start_date = models.DateField(
        verbose_name='Fecha Inicio'
    )
    end_date = models.DateField(
        verbose_name='Fecha Fin'
    )
    # Funciones adicionales (si aplica)
    additional_functions = models.TextField(
        blank=True,
        verbose_name='Funciones Adicionales'
    )

    class Meta:
        db_table = 'app_token_rate_change_detail'
        verbose_name = 'Detalle de Cambio de Tasa'
        verbose_name_plural = 'Detalles de Cambio de Tasa'

    def __str__(self):
        return f"Cambio de tasa - {self.token.display_number}"

    @property
    def rate_difference(self):
        """Calcula la diferencia de tasa"""
        return self.new_rate - self.current_rate

    @property
    def rate_percentage_change(self):
        """Calcula el porcentaje de cambio"""
        if self.current_rate > 0:
            return ((self.new_rate - self.current_rate) / self.current_rate) * 100
        return 0
