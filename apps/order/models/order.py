from django.db import models
from utils.BaseModel import BaseModel
from apps.maintenance.models.distributor_center import DistributorCenter, LocationModel
from apps.user.models.user import UserModel

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

