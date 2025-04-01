
from django.db import models
from utils.BaseModel import BaseModel
from .country import CountryModel
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

    country = models.ForeignKey(
        CountryModel,
        on_delete=models.SET_NULL,
        verbose_name="País",
        related_name="distributor_center_country",
        null=True,
        blank=True,
        default=None)


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.direction = self.direction.upper()
        return super(DistributorCenter, self).save(*args, **kwargs)

    class Meta:
        db_table = "distributor_center"
        verbose_name = "Centro de Distribución"
        verbose_name_plural = "Centros de Distribución"


# Localizaiones de envio de salida de productos, puede ser un cliente o un centro de distribución
class LocationModel(BaseModel):
    name = models.CharField(
        "Nombre",
        max_length=50)
    distributor_center = models.OneToOneField(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        related_name="location_distributor_center",
        null=True,
        blank=True)
    code = models.CharField(
        "Código",
        unique=True,
        max_length=50,
        null=True,
        blank=True,
        error_messages={
            "unique": "Ya existe una localización con este código"
        }
    )

    country = models.ForeignKey(
        CountryModel,
        on_delete=models.SET_NULL,
        verbose_name="País",
        related_name="location_country",
        null=True,
        blank=True,
        default=None)



    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        return super(LocationModel, self).save(*args, **kwargs)

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


# lotes por centro de distribución
class LotModel(BaseModel):
    distributor_center = models.ForeignKey(
        DistributorCenter,
        on_delete=models.SET_NULL,
        verbose_name="Centro de Distribución",
        null=True,
        blank=True)
    code = models.CharField(
        "Código",
        max_length=6)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        return super(LotModel, self).save(*args, **kwargs)

    class Meta:
        db_table = "lot"
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        unique_together = ['distributor_center', 'code']