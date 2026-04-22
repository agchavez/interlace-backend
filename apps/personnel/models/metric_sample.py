"""
Sample de métrica operativa: una fila por evento de truck_cycle convertido
a un valor de un PerformanceMetricType. Alimenta los dashboards del turno y
el histórico en /personnel/performance.
"""
from django.db import models
from .personnel import PersonnelProfile
from .performance_new import PerformanceMetricType


class PersonnelMetricSample(models.Model):
    SOURCE_AUTO = 'AUTO_TRUCK_CYCLE'
    SOURCE_MANUAL = 'MANUAL'
    SOURCE_CHOICES = [
        (SOURCE_AUTO, 'Auto - Truck Cycle'),
        (SOURCE_MANUAL, 'Manual'),
    ]

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='metric_samples',
        verbose_name='Personal',
    )
    metric_type = models.ForeignKey(
        PerformanceMetricType,
        on_delete=models.PROTECT,
        related_name='samples',
        verbose_name='Tipo de métrica',
    )
    operational_date = models.DateField(
        'Fecha operativa',
        db_index=True,
    )
    numeric_value = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=4,
    )
    source = models.CharField(
        'Origen',
        max_length=30,
        choices=SOURCE_CHOICES,
        default=SOURCE_AUTO,
    )
    # Referencia a la pauta (si aplica). No FK formal para evitar dep. circular
    # entre personnel↔truck_cycle.
    pauta_id = models.IntegerField(
        'Pauta id',
        null=True,
        blank=True,
        db_index=True,
    )
    context = models.JSONField(
        'Contexto',
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_personnel_metric_sample'
        verbose_name = 'Sample de métrica'
        verbose_name_plural = 'Samples de métricas'
        indexes = [
            models.Index(fields=['personnel', '-operational_date']),
            models.Index(fields=['metric_type', '-operational_date']),
            models.Index(fields=['operational_date']),
            models.Index(fields=['pauta_id', 'metric_type']),
        ]
        ordering = ['-operational_date', '-created_at']

    def __str__(self):
        return f"{self.personnel.employee_code} · {self.metric_type.code} · {self.numeric_value}"
