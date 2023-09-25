from django.db import models
from apps.maintenance.models.distributor_center import DistributorCenter
import datetime
from apps.maintenance.models.product import ProductModel
from utils.BaseModel import BaseModel

class PeriodModel(BaseModel):
    LABEL_CHICES = (
        ("A","A"),
        ("B","B"),
        ("C","C"),
    )
    label= models.fields.CharField(
        max_length=1, 
        choices=LABEL_CHICES, 
        null=True, 
        blank=True)
    initialDate= models.fields.DateField(
        null=True, 
        blank=True,
        default= datetime.date.today)
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        related_name="period_distributor_center",
        null=True,
        blank=True)
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.SET_NULL,
        verbose_name='Producto',
        related_name="period_product",
        null=True,
        blank=True
    )
    class Meta:
        db_table = "period"
        verbose_name = "Period"
        verbose_name_plural = "Periods"