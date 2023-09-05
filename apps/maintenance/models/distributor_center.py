
from django.db import models
from utils.BaseModel import BaseModel
# Modelo para el mantenimiento de los centros de distribución
class DistributorCenter(models.Model):
    name = models.CharField(
        "Nombre",
        max_length=50)
    direction = models.CharField(
        "Dirección",
        max_length=50, null=True)
    country_code = models.CharField(
        "Código de País",
        max_length=5, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "distributor_center"
        verbose_name = "Centro de Distribución"
        verbose_name_plural = "Centros de Distribución"


# Localizaiones de envio de salida de productos, puede ser un cliente o un centro de distribución
class LocationModel(BaseModel):
    name = models.CharField(
        "Nombre",
        max_length=50)
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        null=True,
        blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "location"
        verbose_name = "Localización"
        verbose_name_plural = "Localizaciones"

# Modelo para las rutas de salida relacion entre un centro de distribución y una localización de salida y con un codigo unico
class RouteModel(BaseModel):
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        null=True,
        blank=True)
    location = models.ForeignKey(
        LocationModel,
        on_delete=models.SET_NULL,
        verbose_name="Localización",
        null=True,
        blank=True)
    code = models.CharField(
        "Código",
        max_length=50)

    def __str__(self):
        return self.code

    class Meta:
        db_table = "route"
        verbose_name = "Ruta"
        verbose_name_plural = "Rutas"
        unique_together = ['distributor_center', 'location', 'code']


