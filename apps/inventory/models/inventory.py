from django.db import models

from utils.BaseModel import BaseModel
from apps.maintenance.models.product import ProductModel
from apps.maintenance.models.distributor_center import DistributorCenter
from apps.user.models.user import UserModel
from apps.tracker.models.tracker import TrackerDetailProductModel
# modelo de movimietos de inventario
class InventoryMovementModel(BaseModel):
    # Modulos donde se registra el movimiento
    class Module(models.TextChoices):
        T1 = "T1", "T1"
        T2 = "T2", "T2"
        ADMIN = "ADMIN", "ADMIN"
        ORDER = "ORDER", "ORDER"
    # tipo de movimiento
    class MovementType(models.TextChoices):
        IN = "IN", "Entrada"
        OUT = "OUT", "Salida"
        BALANCE = "BALANCE", "Balance"

    # detalle del producto de tracker
    tracker_detail_product = models.ForeignKey(
        TrackerDetailProductModel,
        on_delete=models.CASCADE,
        verbose_name="Tracking",
        related_name="inventory_movement_tracking",
        null=True,
        blank=True)

    # Modulo donde se registra el movimiento
    module = models.CharField(
        "Modulo",
        max_length=50,
        choices=Module.choices
    )

    # identificador del origen del movimiento
    origin_id = models.IntegerField(
        "Id de origen",
        null=True,
        blank=True
    )

    # Movimiento aplicado a un inventario
    is_applied = models.BooleanField(
        "Aplicado",
        default=False)

    # Fecha de aplicacion del movimiento
    applied_date = models.DateTimeField(
        "Fecha de aplicación",
        null=True,
        blank=True)

    movement_type = models.CharField(
        "Tipo de movimiento",
        max_length=50,
        choices=MovementType.choices,
        default=MovementType.IN)

    # Motivo del balance
    reason = models.TextField(
        "Motivo",
        null=True,
        blank=True)

    # cantidad inicial antes del movimiento
    initial_quantity = models.IntegerField(
        "Cantidad inicial",
        default=0)

    # cantidad puede ser negativa o positiva
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    # usuario que crea el movimiento
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        related_name="inventory_movement_user")

    class Meta:
        db_table = "inventory_movement"
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"

    def __str__(self):
        return f"{self.id} - {self.tracker_detail_product.tracker_detail.product.name} - {self.quantity}"
