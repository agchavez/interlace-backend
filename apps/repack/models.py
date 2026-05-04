"""
Modelos del módulo Reempaque (tareas de almacén).

Una RepackSession representa un turno de trabajo de un operario:
inicia → digita cajas reempacadas por producto + fecha de vencimiento → termina.
Al cerrar, la métrica `repack_boxes_per_hour` se emite a PersonnelMetricSample
para que aparezca en dashboards y bloques Performers.
"""
from django.db import models
from django.contrib.auth import get_user_model

from utils.BaseModel import BaseModel
from apps.personnel.models.personnel import PersonnelProfile
from apps.maintenance.models.distributor_center import DistributorCenter
from apps.maintenance.models.product import ProductModel


User = get_user_model()


class RepackSession(BaseModel):
    """Sesión de reempaque de un operario en una fecha operativa.

    Un operario puede tener varias sesiones por día (ej. 2:30-3:30 pm y 5-6 pm).
    Cada sesión es un bloque continuo de trabajo que se inicia y se cierra.
    """

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE,    'Activa'),
        (STATUS_COMPLETED, 'Completada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='repack_sessions',
        verbose_name='Operario',
    )
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        related_name='repack_sessions',
        verbose_name='Centro de distribución',
    )
    operational_date = models.DateField('Fecha operativa', db_index=True)
    started_at = models.DateTimeField('Inicio', auto_now_add=True)
    ended_at = models.DateTimeField('Fin', null=True, blank=True)
    status = models.CharField(
        'Estado', max_length=12, choices=STATUS_CHOICES, default=STATUS_ACTIVE,
    )
    notes = models.TextField('Notas', blank=True, default='')
    started_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='repack_sessions_started',
        verbose_name='Iniciada por',
    )

    class Meta:
        db_table = 'repack_session'
        verbose_name = 'Sesión de reempaque'
        verbose_name_plural = 'Sesiones de reempaque'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['personnel', '-operational_date']),
            models.Index(fields=['distributor_center', '-operational_date', 'status']),
        ]

    def __str__(self):
        return f'{self.personnel.full_name} · {self.operational_date} · {self.get_status_display()}'

    @property
    def total_boxes(self) -> int:
        return sum(e.box_count for e in self.entries.all())

    @property
    def duration_seconds(self) -> int:
        if not self.ended_at:
            return 0
        return int((self.ended_at - self.started_at).total_seconds())

    @property
    def boxes_per_hour(self) -> float:
        secs = self.duration_seconds
        if secs <= 0:
            return 0.0
        return round(self.total_boxes * 3600 / secs, 2)


class RepackEntry(BaseModel):
    """Lote individual reempacado dentro de una sesión.

    El operario digita: producto + cantidad de cajas + fecha de vencimiento.
    Una sesión puede tener N entries (ej. 50 cajas leche venc 2026-12 +
    30 cajas yogurt venc 2026-08 = 2 entries).
    """

    session = models.ForeignKey(
        RepackSession,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name='Sesión',
    )
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='repack_entries',
        verbose_name='Producto',
    )
    material_code = models.CharField('Código de material', max_length=40)
    product_name = models.CharField('Nombre del producto', max_length=200, blank=True, default='')
    box_count = models.PositiveIntegerField('Cantidad de cajas')
    expiration_date = models.DateField('Fecha de vencimiento')
    notes = models.CharField('Notas', max_length=200, blank=True, default='')

    class Meta:
        db_table = 'repack_entry'
        verbose_name = 'Entrada de reempaque'
        verbose_name_plural = 'Entradas de reempaque'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['material_code']),
            models.Index(fields=['expiration_date']),
        ]

    def __str__(self):
        return f'{self.material_code} · {self.box_count} cajas · venc {self.expiration_date}'
