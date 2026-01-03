"""
Modelos de métricas de desempeño
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .personnel import PersonnelProfile


class PerformanceMetric(models.Model):
    """
    Métricas de productividad y desempeño del personal
    """
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'

    PERIOD_CHOICES = [
        (DAILY, 'Diario'),
        (WEEKLY, 'Semanal'),
        (MONTHLY, 'Mensual'),
    ]

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='performance_metrics',
        verbose_name='Personal'
    )
    metric_date = models.DateField(
        verbose_name='Fecha de la métrica',
        db_index=True
    )
    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        default=DAILY,
        verbose_name='Período',
        db_index=True
    )

    # Métricas operativas
    pallets_moved = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Pallets movidos',
        help_text='Cantidad de pallets procesados'
    )
    hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Horas trabajadas'
    )
    productivity_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Tasa de productividad',
        help_text='Pallets por hora (calculado automáticamente)'
    )

    # Indicadores de calidad
    errors_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad de errores',
        help_text='Errores o incidencias registradas'
    )
    accidents_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Accidentes',
        help_text='Accidentes de trabajo'
    )

    # Evaluación del supervisor
    supervisor_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Calificación del supervisor',
        help_text='Escala de 1 a 5'
    )
    supervisor_comments = models.TextField(
        blank=True,
        verbose_name='Comentarios del supervisor'
    )
    evaluated_by = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations_given',
        verbose_name='Evaluado por'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_performance_metric'
        verbose_name = 'Métrica de Desempeño'
        verbose_name_plural = 'Métricas de Desempeño'
        ordering = ['-metric_date']
        indexes = [
            models.Index(fields=['personnel', '-metric_date']),
            models.Index(fields=['period', '-metric_date']),
        ]
        unique_together = [['personnel', 'metric_date', 'period']]

    def __str__(self):
        return f"{self.personnel.employee_code} - {self.metric_date} - {self.get_period_display()}"

    def save(self, *args, **kwargs):
        # Calcular productividad automáticamente
        if self.hours_worked and self.hours_worked > 0:
            self.productivity_rate = self.pallets_moved / float(self.hours_worked)
        else:
            self.productivity_rate = 0
        super().save(*args, **kwargs)

    @property
    def performance_score(self):
        """Calcula un score de desempeño general"""
        score = 0
        # Productividad (40%)
        if self.productivity_rate:
            score += min(self.productivity_rate / 20 * 40, 40)
        # Calidad (30%) - inverso de errores
        if self.errors_count == 0:
            score += 30
        else:
            score += max(30 - (self.errors_count * 5), 0)
        # Seguridad (15%) - sin accidentes
        if self.accidents_count == 0:
            score += 15
        # Evaluación supervisor (15%)
        if self.supervisor_rating:
            score += (self.supervisor_rating / 5) * 15
        return round(score, 2)
