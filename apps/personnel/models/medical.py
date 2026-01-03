"""
Modelos de historial médico
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from .personnel import PersonnelProfile


def medical_document_path(instance, filename):
    """Ruta para documentos médicos"""
    return f'personnel/medical/{instance.personnel.employee_code}/{filename}'


class MedicalRecord(models.Model):
    """
    Registros médicos del personal
    """
    CONDITION = 'CONDITION'
    CLINIC_PASS = 'CLINIC_PASS'
    INCAPACITY = 'INCAPACITY'
    CHECKUP = 'CHECKUP'

    RECORD_TYPE_CHOICES = [
        (CONDITION, 'Condición Médica'),
        (CLINIC_PASS, 'Pase de Clínica'),
        (INCAPACITY, 'Incapacidad'),
        (CHECKUP, 'Chequeo Médico'),
    ]

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name='Personal'
    )
    record_type = models.CharField(
        max_length=20,
        choices=RECORD_TYPE_CHOICES,
        verbose_name='Tipo de registro',
        db_index=True
    )
    record_date = models.DateField(
        verbose_name='Fecha del registro',
        db_index=True
    )
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción general del evento médico'
    )
    diagnosis = models.TextField(
        blank=True,
        verbose_name='Diagnóstico',
        help_text='Diagnóstico médico (si aplica)'
    )

    # Fechas relevantes
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de inicio',
        help_text='Para incapacidades o tratamientos'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de fin',
        help_text='Fecha esperada de retorno'
    )

    # Información médica
    doctor_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre del médico'
    )
    clinic_hospital = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Clínica/Hospital'
    )

    # Documento adjunto
    document = models.FileField(
        upload_to=medical_document_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            )
        ],
        verbose_name='Documento médico',
        help_text='PDF o imagen del documento médico'
    )

    # Seguimiento
    requires_followup = models.BooleanField(
        default=False,
        verbose_name='Requiere seguimiento'
    )
    followup_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de seguimiento'
    )

    # Privacidad
    is_confidential = models.BooleanField(
        default=True,
        verbose_name='Confidencial',
        help_text='Solo accesible por personal autorizado'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_records_created',
        verbose_name='Registrado por'
    )

    class Meta:
        db_table = 'app_personnel_medical_record'
        verbose_name = 'Registro Médico'
        verbose_name_plural = 'Registros Médicos'
        ordering = ['-record_date']
        indexes = [
            models.Index(fields=['personnel', '-record_date']),
            models.Index(fields=['record_type', '-record_date']),
        ]
        permissions = [
            ('view_confidential_medical', 'Puede ver registros médicos confidenciales'),
        ]

    def __str__(self):
        return f"{self.personnel.employee_code} - {self.get_record_type_display()} - {self.record_date}"

    @property
    def is_active_incapacity(self):
        """Verifica si es una incapacidad activa"""
        from datetime import date
        if self.record_type != self.INCAPACITY:
            return False
        if not self.end_date:
            return True
        return self.end_date >= date.today()
