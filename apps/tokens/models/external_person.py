"""
Modelo para personas externas (proveedores, visitantes).
Usado principalmente para pases de salida de materiales.
"""
from django.db import models
from utils.BaseModel import BaseModel


class ExternalPerson(BaseModel):
    """
    Persona externa (proveedor, visitante) para pases de salida.

    Permite registrar proveedores que recogen materiales del CD
    (ej: recicladores, proveedores de servicios, etc.)
    """

    name = models.CharField(
        max_length=200,
        verbose_name='Nombre completo'
    )
    company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Empresa'
    )
    identification = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Identificación',
        help_text='Número de identidad o RTN'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

    class Meta:
        db_table = 'app_token_external_person'
        verbose_name = 'Persona Externa'
        verbose_name_plural = 'Personas Externas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.company:
            return f"{self.name} ({self.company})"
        return self.name
