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
    # Costo estandar
    standard_cost = models.DecimalField(
        "Costo estándar",
        max_digits=10,
        decimal_places=2,
        default=0)
    # pre-bloqueo
    pre_block = models.IntegerField(
        "Pre-bloqueo",
        default=0)
    # bloqueo
    block = models.IntegerField(
        "Bloqueo",
        default=0)
    # dias para pre-bloqueo
    pre_block_days = models.IntegerField(
        "Días para pre-bloqueo",
        default=0)
    # dias proximo pre-bloqueo
    pre_block_days_next = models.IntegerField(
        "Días próximo pre-bloqueo",
        default=0)
    # dias para bloqueo
    block_days = models.IntegerField(
        "Días para bloqueo",
        default=0)
    # codigo caracteristica
    code_feature = models.CharField(
        "Código",
        max_length=50,
        unique=True,
        error_messages={
            'unique': "Ya existe un producto con este código."
        })
    # division
    division = models.CharField(
        "División",
        max_length=50)
    # clase
    class_product = models.CharField(
        "Clase",
        max_length=50)
    # tamaño
    size = models.CharField(
        "Tamaño",
        max_length=50)
    # empaque
    packaging = models.CharField(
        "Empaque",
        max_length=50)
    # helectrolitos
    helectrolitos = models.DecimalField(
        "Helectrolitos",
        max_digits=14,
        decimal_places=10,
        default=0)
    # HL por unidad
    hl_per_unit = models.DecimalField(
        "HL por unidad",
        max_digits=14,
        decimal_places=10,
        default=0,
        blank=True,
    )
    # concadenado tipo
    concadenated_type = models.CharField(
        "Tipo concadenado",
        max_length=50)
    # costo
    cost = models.DecimalField(
        "Costo",
        max_digits=12,
        decimal_places=8,
        default=0)
    # descripcion sap
    description_sap = models.CharField(
        "Descripción SAP",
        max_length=100)
    # Lib a ton
    lib_to_ton = models.DecimalField(
        "Lib a ton",
        max_digits=14,
        decimal_places=10,
        default=0)
    # Peso
    weight = models.DecimalField(
        "Peso",
        max_digits=10,
        decimal_places=2,
        default=0)
    # ton
    ton = models.DecimalField(
        "Ton",
        max_digits=14,
        decimal_places=10,
        default=0)
    # bloqueo para t1
    block_t1 = models.IntegerField(
        "Bloqueo T1",
        default=0)
    # dias para no aceptar producto
    days_not_accept_product = models.IntegerField(
        "Días para no aceptar producto",
        default=0)
    
    # producto de salida
    is_output = models.BooleanField(
        "Es de Salida",
        default=False
    )

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


# Modelo para el mantenimiento de los tipos de salida de productos
class OutputTypeModel(BaseModel):
    name = models.CharField(
        "Nombre",
        max_length=50)
    required_details = models.BooleanField(
        "Detalle requeridos",
        default=False)
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        return super(OutputTypeModel, self).save(*args, **kwargs)

    class Meta:
        db_table = "output_type"
        verbose_name = "Tipo de salida"
        verbose_name_plural = "Tipos de salida"
