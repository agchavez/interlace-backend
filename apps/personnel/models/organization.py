"""
Modelos de estructura organizacional
"""
from django.db import models
from django.core.validators import MinLengthValidator


class Area(models.Model):
    """
    Áreas de negocio de la organización
    """
    OPERATIONS = 'OPERATIONS'
    ADMINISTRATION = 'ADMINISTRATION'
    PEOPLE = 'PEOPLE'
    SECURITY = 'SECURITY'
    DELIVERY = 'DELIVERY'

    AREA_CHOICES = [
        (OPERATIONS, 'Operaciones'),
        (ADMINISTRATION, 'Administración'),
        (PEOPLE, 'People/RRHH'),
        (SECURITY, 'Seguridad'),
        (DELIVERY, 'Delivery/Despachos'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        choices=AREA_CHOICES,
        verbose_name='Código de área'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_area'
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['name']

    def __str__(self):
        return self.get_code_display()


class Department(models.Model):
    """
    Departamentos dentro de las áreas
    """
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name='departments',
        verbose_name='Área'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre del departamento'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(2)],
        verbose_name='Código'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_department'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['area', 'name']
        unique_together = [['area', 'code']]

    def __str__(self):
        return f"{self.area.get_code_display()} - {self.name}"
