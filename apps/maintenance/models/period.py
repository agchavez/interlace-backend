from django.db import models
from apps.maintenance.models.distributor_center import DistributorCenter
from datetime import date

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
        default=date.today())
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        related_name="period_distributor_center",
        null=True,
        blank=True)
    
    class Meta:
        db_table = "period"
        verbose_name = "Period"
        verbose_name_plural = "Periods"