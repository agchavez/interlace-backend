"""
Nuevos modelos de desempeño con métricas escalables
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from .personnel import PersonnelProfile


class PerformanceMetricType(models.Model):
    """
    Tipo de métrica de desempeño configurable

    Permite definir métricas personalizadas que se pueden asignar
    a diferentes tipos de posición
    """
    NUMERIC = 'NUMERIC'
    RATING = 'RATING'  # 1-5 estrellas
    PERCENTAGE = 'PERCENTAGE'
    BOOLEAN = 'BOOLEAN'
    TEXT = 'TEXT'

    METRIC_TYPE_CHOICES = [
        (NUMERIC, 'Numérico'),
        (RATING, 'Calificación (1-5)'),
        (PERCENTAGE, 'Porcentaje (0-100)'),
        (BOOLEAN, 'Sí/No'),
        (TEXT, 'Texto'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la métrica',
        help_text='Ej: Productividad, Pallets movidos, Calidad, etc.'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Código único para identificar la métrica (snake_case)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción de qué mide esta métrica'
    )
    metric_type = models.CharField(
        max_length=20,
        choices=METRIC_TYPE_CHOICES,
        default=NUMERIC,
        verbose_name='Tipo de métrica'
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Unidad',
        help_text='Ej: pallets, horas, %, etc.'
    )

    # Valores mínimos y máximos (para validación)
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor mínimo',
        help_text='Valor mínimo permitido (opcional)'
    )
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor máximo',
        help_text='Valor máximo permitido (opcional)'
    )

    # Configuración de peso para cálculo de score general
    weight = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Peso',
        help_text='Peso de esta métrica en el cálculo del score general (0-100)'
    )

    # Posiciones a las que aplica
    applicable_position_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Tipos de posición aplicables',
        help_text='Lista de position_type donde aplica esta métrica'
    )

    # Configuración
    is_required = models.BooleanField(
        default=True,
        verbose_name='Es requerida',
        help_text='Si esta métrica es obligatoria en la evaluación'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        db_index=True
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Orden de visualización',
        help_text='Orden en que se muestra en el formulario'
    )

    # Ayuda para el evaluador
    help_text = models.TextField(
        blank=True,
        verbose_name='Texto de ayuda',
        help_text='Instrucciones para el evaluador'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='metric_types_created',
        verbose_name='Creado por'
    )

    class Meta:
        db_table = 'app_personnel_metric_type'
        verbose_name = 'Tipo de Métrica de Desempeño'
        verbose_name_plural = 'Tipos de Métricas de Desempeño'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"

    def is_applicable_for_position(self, position_type):
        """Verifica si esta métrica aplica para un tipo de posición"""
        if not self.applicable_position_types:
            return True  # Si no hay restricciones, aplica para todos
        return position_type in self.applicable_position_types


class PerformanceEvaluation(models.Model):
    """
    Evaluación de desempeño general

    Contiene la información general de una evaluación.
    Las métricas específicas se almacenan en EvaluationMetricValue
    """
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'
    QUARTERLY = 'QUARTERLY'
    ANNUAL = 'ANNUAL'

    PERIOD_CHOICES = [
        (WEEKLY, 'Semanal'),
        (MONTHLY, 'Mensual'),
        (QUARTERLY, 'Trimestral'),
        (ANNUAL, 'Anual'),
    ]

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='Personal evaluado'
    )
    evaluation_date = models.DateField(
        verbose_name='Fecha de evaluación',
        db_index=True
    )
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        default=MONTHLY,
        verbose_name='Período'
    )

    # Evaluador
    evaluated_by = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations_conducted',
        verbose_name='Evaluado por'
    )

    # Score general calculado
    overall_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='Puntuación general',
        help_text='Calculado automáticamente basado en las métricas (0-5)'
    )

    # Comentarios generales
    comments = models.TextField(
        blank=True,
        verbose_name='Comentarios generales'
    )

    # Estado
    is_draft = models.BooleanField(
        default=True,
        verbose_name='Es borrador',
        help_text='Evaluación aún no finalizada'
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de envío',
        help_text='Cuando se finalizó la evaluación'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_evaluation'
        verbose_name = 'Evaluación de Desempeño'
        verbose_name_plural = 'Evaluaciones de Desempeño'
        ordering = ['-evaluation_date']
        indexes = [
            models.Index(fields=['personnel', '-evaluation_date']),
            models.Index(fields=['period', '-evaluation_date']),
            models.Index(fields=['is_draft']),
        ]

    def __str__(self):
        return f"{self.personnel.employee_code} - {self.evaluation_date} - {self.get_period_display()}"

    def calculate_overall_score(self):
        """
        Calcula el score general basado en las métricas con peso
        Normaliza a escala 0-5
        """
        metrics = self.metric_values.select_related('metric_type').all()

        if not metrics:
            return None

        total_weight = 0
        weighted_sum = 0

        for metric_value in metrics:
            metric_type = metric_value.metric_type
            if metric_type.weight == 0:
                continue

            # Normalizar el valor a escala 0-5
            normalized_value = metric_value.get_normalized_value()
            if normalized_value is not None:
                weighted_sum += normalized_value * metric_type.weight
                total_weight += metric_type.weight

        if total_weight == 0:
            return None

        # Calcular promedio ponderado
        score = (weighted_sum / total_weight)
        return round(score, 2)

    def save(self, *args, **kwargs):
        # Calcular score general antes de guardar
        if not self.is_draft:
            self.overall_score = self.calculate_overall_score()
        super().save(*args, **kwargs)


class EvaluationMetricValue(models.Model):
    """
    Valor de una métrica específica para una evaluación
    """
    evaluation = models.ForeignKey(
        PerformanceEvaluation,
        on_delete=models.CASCADE,
        related_name='metric_values',
        verbose_name='Evaluación'
    )
    metric_type = models.ForeignKey(
        PerformanceMetricType,
        on_delete=models.PROTECT,
        related_name='values',
        verbose_name='Tipo de métrica'
    )

    # Valores según tipo de métrica
    numeric_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor numérico'
    )
    text_value = models.TextField(
        blank=True,
        verbose_name='Valor de texto'
    )
    boolean_value = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Valor booleano'
    )

    # Comentarios específicos de esta métrica
    comments = models.TextField(
        blank=True,
        verbose_name='Comentarios'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_evaluation_metric_value'
        verbose_name = 'Valor de Métrica'
        verbose_name_plural = 'Valores de Métricas'
        unique_together = [['evaluation', 'metric_type']]

    def __str__(self):
        return f"{self.evaluation.personnel.employee_code} - {self.metric_type.name}: {self.get_display_value()}"

    def get_display_value(self):
        """Retorna el valor en formato legible"""
        if self.metric_type.metric_type == PerformanceMetricType.NUMERIC:
            return f"{self.numeric_value} {self.metric_type.unit}".strip()
        elif self.metric_type.metric_type == PerformanceMetricType.RATING:
            return f"{self.numeric_value}/5"
        elif self.metric_type.metric_type == PerformanceMetricType.PERCENTAGE:
            return f"{self.numeric_value}%"
        elif self.metric_type.metric_type == PerformanceMetricType.BOOLEAN:
            return "Sí" if self.boolean_value else "No"
        elif self.metric_type.metric_type == PerformanceMetricType.TEXT:
            return self.text_value or ""
        return ""

    def get_normalized_value(self):
        """
        Normaliza el valor a escala 0-5 para cálculo de score
        """
        metric_type = self.metric_type

        if metric_type.metric_type == PerformanceMetricType.RATING:
            # Ya está en escala 1-5, ajustar a 0-5
            return self.numeric_value if self.numeric_value else 0

        elif metric_type.metric_type == PerformanceMetricType.PERCENTAGE:
            # Convertir porcentaje 0-100 a escala 0-5
            return (self.numeric_value / 20) if self.numeric_value else 0

        elif metric_type.metric_type == PerformanceMetricType.BOOLEAN:
            # Sí = 5, No = 0
            return 5 if self.boolean_value else 0

        elif metric_type.metric_type == PerformanceMetricType.NUMERIC:
            # Normalizar según min/max si están definidos
            if metric_type.min_value is not None and metric_type.max_value is not None:
                if self.numeric_value is None:
                    return 0
                # Normalizar a 0-5
                value_range = float(metric_type.max_value - metric_type.min_value)
                if value_range == 0:
                    return 5
                normalized = ((self.numeric_value - metric_type.min_value) / value_range) * 5
                return max(0, min(5, normalized))
            else:
                # Sin min/max, asumir valor directo en escala 0-5
                return min(5, max(0, self.numeric_value)) if self.numeric_value else 0

        return 0
