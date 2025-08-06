from django.db import models
from utils.BaseModel import BaseModel
from apps.maintenance.models.product import ProductModel
from apps.maintenance.models.distributor_center import DistributorCenter

# Modelo para manejar inventario directo de productos por centro de distribución
class ProductInventoryModel(BaseModel):
    # Producto
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        verbose_name="Producto",
        related_name="product_inventory")

    # Centro de distribución
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.CASCADE,
        verbose_name="Centro de distribución",
        related_name="product_inventory")

    # Fecha de vencimiento
    expiration_date = models.DateField(
        "Fecha de vencimiento",
        null=True,
        blank=True)

    # Cantidad total en inventario
    total_quantity = models.IntegerField(
        "Cantidad total",
        default=0)

    # Cantidad disponible para órdenes
    available_quantity = models.IntegerField(
        "Cantidad disponible",
        default=0)

    # Cantidad reservada en órdenes pendientes
    reserved_quantity = models.IntegerField(
        "Cantidad reservada",
        default=0)

    class Meta:
        db_table = "product_inventory"
        verbose_name = "Inventario de producto"
        verbose_name_plural = "Inventarios de productos"
        unique_together = ('product', 'distributor_center', 'expiration_date')

    def __str__(self):
        return f"{self.product.name} - {self.distributor_center.name} - {self.available_quantity}"

    def reserve_quantity(self, quantity):
        """Reserva cantidad para una orden"""
        if quantity > self.available_quantity:
            raise ValueError("No hay suficiente cantidad disponible")
        
        self.available_quantity -= quantity
        self.reserved_quantity += quantity
        self.save()

    def release_quantity(self, quantity):
        """Libera cantidad reservada (cancelación de orden)"""
        if quantity > self.reserved_quantity:
            raise ValueError("No se puede liberar más cantidad de la reservada")
        
        self.reserved_quantity -= quantity
        self.available_quantity += quantity
        self.save()

    def consume_quantity(self, quantity):
        """Consume cantidad reservada (orden completada)"""
        if quantity > self.reserved_quantity:
            raise ValueError("No se puede consumir más cantidad de la reservada")
        
        self.reserved_quantity -= quantity
        self.total_quantity -= quantity
        self.save()

    def add_inventory(self, quantity):
        """Agrega inventario (entrada de productos)"""
        self.total_quantity += quantity
        self.available_quantity += quantity
        self.save()