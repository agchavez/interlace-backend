"""
Modelos de certificaciones del personal
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from datetime import date, timedelta
from .personnel import PersonnelProfile
from apps.core.azure_utils import generate_blob_sas_url


def certification_document_path(instance, filename):
    """Ruta para certificados"""
    return f'personnel/certifications/{instance.personnel.employee_code}/{filename}'


def certification_signature_path(instance, filename):
    """Ruta para firmas de certificaciones"""
    return f'personnel/certifications/signatures/{instance.personnel.employee_code}/{filename}'


class CertificationType(models.Model):
    """
    Tipos de certificaciones disponibles
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la certificación'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    validity_period_days = models.IntegerField(
        default=365,
        verbose_name='Período de validez (días)',
        help_text='Días hasta que expire la certificación'
    )
    requires_renewal = models.BooleanField(
        default=True,
        verbose_name='Requiere renovación'
    )
    is_mandatory = models.BooleanField(
        default=False,
        verbose_name='Es obligatoria',
        help_text='Certificación obligatoria para ciertos puestos'
    )
    applicable_positions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Posiciones aplicables',
        help_text='Lista de position_type donde aplica'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_certification_type'
        verbose_name = 'Tipo de Certificación'
        verbose_name_plural = 'Tipos de Certificación'
        ordering = ['name']

    def __str__(self):
        return self.name


class Certification(models.Model):
    """
    Certificaciones y entrenamientos del personal
    """
    # Estados de progreso
    STATUS_PENDING = 'PENDING'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_NOT_COMPLETED = 'NOT_COMPLETED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_IN_PROGRESS, 'En Progreso'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_NOT_COMPLETED, 'No Completó'),
    ]

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='certifications',
        verbose_name='Personal'
    )
    certification_type = models.ForeignKey(
        CertificationType,
        on_delete=models.PROTECT,
        related_name='certifications',
        verbose_name='Tipo de certificación'
    )
    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Número de certificación',
        help_text='Número de registro o identificación del certificado'
    )
    issuing_authority = models.CharField(
        max_length=200,
        verbose_name='Autoridad emisora',
        help_text='Institución que emite el certificado'
    )
    issue_date = models.DateField(
        verbose_name='Fecha de emisión',
        db_index=True
    )
    expiration_date = models.DateField(
        verbose_name='Fecha de vencimiento',
        db_index=True
    )

    # Documento del certificado
    certificate_document = models.FileField(
        upload_to=certification_document_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            )
        ],
        verbose_name='Documento del certificado'
    )

    # Estado
    is_valid = models.BooleanField(
        default=True,
        verbose_name='Válida',
        help_text='Si la certificación está vigente y válida',
        db_index=True
    )
    revoked = models.BooleanField(
        default=False,
        verbose_name='Revocada'
    )
    revocation_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de revocación'
    )
    revocation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de revocación'
    )

    # Renovación
    renewal_notification_sent = models.BooleanField(
        default=False,
        verbose_name='Notificación de renovación enviada'
    )
    renewal_notification_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de notificación'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    # Flujo de progreso
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Estado',
        db_index=True
    )

    # Completado con firma
    signature = models.ImageField(
        upload_to=certification_signature_path,
        null=True,
        blank=True,
        verbose_name='Firma del participante'
    )
    completion_notes = models.TextField(
        blank=True,
        verbose_name='Notas de completado'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de completado'
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certifications_completed',
        verbose_name='Completado por'
    )

    # No completado
    non_completion_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de no completado'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certifications_created',
        verbose_name='Registrado por'
    )

    class Meta:
        db_table = 'app_personnel_certification'
        verbose_name = 'Certificación'
        verbose_name_plural = 'Certificaciones'
        ordering = ['-expiration_date']
        indexes = [
            models.Index(fields=['personnel', '-expiration_date']),
            models.Index(fields=['is_valid', 'expiration_date']),
            models.Index(fields=['certification_type', 'is_valid']),
        ]
        unique_together = [
            ['personnel', 'certification_type', 'certification_number']
        ]

    def __str__(self):
        return f"{self.personnel.employee_code} - {self.certification_type.name}"

    @property
    def days_until_expiration(self):
        """Días hasta que expire la certificación"""
        if not self.expiration_date:
            return None
        delta = self.expiration_date - date.today()
        return delta.days

    @property
    def is_expiring_soon(self):
        """Verifica si expira en los próximos 30 días"""
        days = self.days_until_expiration
        return days is not None and 0 <= days <= 30

    @property
    def is_expired(self):
        """Verifica si ya expiró"""
        return self.expiration_date < date.today()

    @property
    def status_display(self):
        """Retorna el estado de la certificación (prioriza el flujo de progreso)"""
        # Primero mostrar el estado del flujo
        if self.status == self.STATUS_COMPLETED:
            return 'Completado'
        if self.status == self.STATUS_NOT_COMPLETED:
            return 'No Completó'
        if self.status == self.STATUS_IN_PROGRESS:
            return 'En Progreso'
        if self.status == self.STATUS_PENDING:
            # Si está pendiente, mostrar validez del certificado si aplica
            if self.revoked:
                return 'Revocada'
            if not self.is_valid:
                return 'Inválida'
            if self.is_expired:
                return 'Vencida'
            if self.is_expiring_soon:
                return 'Por vencer'
            return 'Pendiente'
        return 'Vigente'

    @property
    def signature_url(self):
        """Retorna la URL de la firma con SAS token"""
        if not self.signature:
            return None
        try:
            return generate_blob_sas_url(self.signature.name, expiry_hours=2)
        except Exception as e:
            print(f"Error generando URL con SAS token para firma {self.id}: {str(e)}")
            return None

    @property
    def certificate_document_url(self):
        """Retorna la URL del documento con SAS token"""
        if not self.certificate_document:
            return None
        try:
            # Generar URL con SAS token válido por 2 horas
            return generate_blob_sas_url(self.certificate_document.name, expiry_hours=2)
        except Exception as e:
            print(f"Error generando URL con SAS token para certificado {self.id}: {str(e)}")
            return None

    def save(self, *args, **kwargs):
        # Actualizar is_valid basado en fecha de vencimiento y estado de revocación
        if self.revoked:
            self.is_valid = False
        elif self.expiration_date < date.today():
            self.is_valid = False
        else:
            # Si no está revocada y no ha expirado, es válida
            self.is_valid = True
        super().save(*args, **kwargs)
