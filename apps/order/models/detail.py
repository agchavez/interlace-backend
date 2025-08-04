from django.db import models
from utils.BaseModel import BaseModel
from .order import OrderModel

from apps.tracker.models import TrackerDetailProductModel
from apps.maintenance.models.product import ProductModel
from apps.maintenance.models.distributor_center import DistributorCenter

# Detalles de la orden de salida de producto ademas del la cantidad disponble para seleccionar en los TRACKINGS
class OrderDetailModel(BaseModel):
    # orden de salida de producto
    order = models.ForeignKey(
        OrderModel,
        on_delete=models.CASCADE,
        verbose_name="Orden",
        related_name="order_detail")

    # OPCIÓN 1: Con tracker (mantiene funcionalidad actual)
    tracker_detail_product = models.ForeignKey(
        TrackerDetailProductModel,
        on_delete=models.CASCADE,
        verbose_name="Tracker detail product",
        related_name='order_detail_tracker_detail_product',
        null=True,
        blank=True)

    # OPCIÓN 2: Solo producto directo (nueva funcionalidad)
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        verbose_name="Producto",
        related_name='order_detail_product',
        null=True,
        blank=True)

    # Centro de distribución para productos directos
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de distribución",
        related_name='order_detail_distributor_center',
        null=True,
        blank=True)

    # Fecha de vencimiento para productos directos
    expiration_date = models.DateField(
        "Fecha de vencimiento",
        null=True,
        blank=True)

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
        # Constraint: debe tener tracker_detail_product O product (no ambos)
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(tracker_detail_product__isnull=False, product__isnull=True) |
                    models.Q(tracker_detail_product__isnull=True, product__isnull=False)
                ),
                name='order_detail_single_product_source'
            )
        ]

    def __str__(self):
        if self.tracker_detail_product:
            product_name = self.tracker_detail_product.tracker_detail.product.name
        else:
            product_name = self.product.name if self.product else "Sin producto"
        return f"{self.order.distributor_center.name} - {product_name} - {self.quantity}"

    def get_product(self):
        """Helper method to get the product regardless of the source"""
        if self.tracker_detail_product:
            return self.tracker_detail_product.tracker_detail.product
        return self.product

    def get_distributor_center(self):
        """Helper method to get the distributor center"""
        if self.tracker_detail_product:
            return self.tracker_detail_product.tracker_detail.tracker.distributor_center
        return self.distributor_center
