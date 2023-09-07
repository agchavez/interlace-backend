from django.db import models

# local
from utils.BaseModel import BaseModel


# Modelo para el mantenimiento de los productos
class ProductModel(BaseModel):
    name = models.CharField(
        "Nombre",
        max_length=50)
    sap_code = models.CharField(
        "Código SAP",
        max_length=10,
        unique=True)
    brand = models.CharField(
        "Marca",
        max_length=50)
    boxes_pre_pallet = models.IntegerField(
        "Cajas por pallet",
        default=0)
    useful_life = models.IntegerField(
        "Vida útil",
        default=0)
    bar_code = models.CharField(
        "Código de barras",
        max_length=50,
        unique=True)

    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.brand = self.brand.upper()
        return super(ProductModel, self).save(*args, **kwargs)


    class Meta:
        db_table = "product"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

