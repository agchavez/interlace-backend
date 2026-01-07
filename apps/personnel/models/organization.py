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
        null=True,
        blank=True,
        validators=[MinLengthValidator(2)],
        verbose_name='Código',
        help_text='Se genera automáticamente si no se proporciona'
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

    def __str__(self):
        return f"{self.area.get_code_display()} - {self.name}"

    def _generate_code(self):
        """
        Genera un código único para el departamento
        Formato: DEPT-{AREA_PREFIX}-{SEQUENTIAL}
        """
        area_prefix = self.area.code[:3].upper()

        # Obtener el número secuencial más alto para este área
        existing_depts = Department.objects.filter(
            code__startswith=f'DEPT-{area_prefix}-'
        ).order_by('-code')

        if existing_depts.exists():
            last_code = existing_depts.first().code
            try:
                last_number = int(last_code.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Generar el código
        code = f'DEPT-{area_prefix}-{next_number:03d}'

        # Verificar que sea único
        while Department.objects.filter(code=code).exists():
            next_number += 1
            code = f'DEPT-{area_prefix}-{next_number:03d}'

        return code

    def save(self, *args, **kwargs):
        """Auto-generar código si no se proporciona"""
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)
