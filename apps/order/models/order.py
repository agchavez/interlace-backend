from django.db import models
from utils.BaseModel import BaseModel
from apps.maintenance.models.product import ProductModel
from apps.maintenance.models.distributor_center import DistributorCenter, LocationModel
from apps.user.models.user import UserModel
from apps.tracker.models.tracker import TrackerModel
from apps.tracker.models import TrackerDetailProductModel
# Modelo de ordenes de salida de producto
class OrderModel(BaseModel):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        IN_PROCESS = 'IN_PROCESS', 'En proceso'
        COMPLETED = 'COMPLETED', 'Completada'

    # centro de distribucion
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de distribución",
        related_name="order_distributor_center")

    # usuario que crea la orden
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        related_name="order_user")


    # estado de la orden
    status = models.CharField(
        "Estado",
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING)

    # Observaciones
    observations = models.TextField(
        "Observaciones",
        blank=True,
        null=True)

    # localidad de entrega
    location = models.ForeignKey(
        LocationModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Localidad",
        related_name="order_location")

    class Meta:
        db_table = "order"
        verbose_name = "Orden"
        verbose_name_plural = "Ordenes"

    def __str__(self):
        return self.distributor_center.name + " - " + self.user.first_name + " " + self.user.last_name + ' id=' + str(self.id)


# Detalles de la orden de salida de producto ademas del la cantidad disponble para seleccionar en los TRACKINGS
class OrderDetailModel(BaseModel):
    # orden de salida de producto
    order = models.ForeignKey(
        OrderModel,
        on_delete=models.CASCADE,
        verbose_name="Orden",
        related_name="order_detail")

    # tracker detail product
    tracker_detail_product = models.ForeignKey(
        TrackerDetailProductModel,
        on_delete=models.CASCADE,
        verbose_name="Tracker detail product",
        related_name='order_detail_tracker_detail_product',
        default = None)

    # cantidad de producto
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    # cantidad disponible para seleccionar en los TRACKINGS
    quantity_available = models.IntegerField(
        "Cantidad disponible",
        default=0)

    class Meta:
        db_table = "order_detail"
        verbose_name = "Detalle de orden"
        verbose_name_plural = "Detalles de ordenes"
        unique_together = ('order', 'tracker_detail_product')

    def __str__(self):
        return self.order.distributor_center.name + " - " + " - " + str(self.quantity)

# Historico de ordenes de salida de producto con los TRACKINGS
class OrderHistoryModel(BaseModel):
    # orden de salida de producto
    order_detail = models.ForeignKey(
        OrderDetailModel,
        on_delete=models.CASCADE,
        verbose_name="Orden detalle",
        related_name="order_detail_history")

    # tracker
    tracker = models.ForeignKey(
        TrackerModel,
        on_delete=models.CASCADE,
        verbose_name="Tracker",
        related_name="order_history_tracker")

    # cantidad de producto
    quantity = models.IntegerField(
        "Cantidad",
        default=0)

    class Meta:
        db_table = "order_history"
        verbose_name = "Historico de orden"
        verbose_name_plural = "Historicos de ordenes"

    def __str__(self):
        return self.order_detail.order.distributor_center.name + " - " + self.order_detail.product.name + " - " + str(self.quantity)