from apps.tracker.models.tracker import TrackerModel

from django.db import models
from utils.BaseModel import BaseModel

from .detail import OrderDetailModel
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