from django.db import models
from utils.BaseModel import BaseModel
from .order import OrderModel

from apps.tracker.models import TrackerDetailProductModel

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
