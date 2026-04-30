"""
Modelos operativos del ciclo del camión
"""
from django.db import models
from django.contrib.auth import get_user_model
from utils.BaseModel import BaseModel
from apps.personnel.models.personnel import PersonnelProfile
from .core import PautaModel
from .catalogs import BayModel

User = get_user_model()


class PautaAssignmentModel(models.Model):
    """Asignaciones de personal a pautas"""

    ROLE_CHOICES = [
        ('PICKER', 'Picker'),
        ('COUNTER', 'Contador'),
        ('YARD_DRIVER', 'Conductor de Patio'),
        ('DELIVERY_DRIVER', 'Chofer Vendedor'),
        ('OPM', 'OPM'),
        ('VERIFIER', 'Verificador'),
        ('SECURITY', 'Seguridad'),
        ('OPERATIONS', 'Operaciones'),
    ]

    role = models.CharField(
        "Rol",
        max_length=20,
        choices=ROLE_CHOICES,
    )
    assigned_at = models.DateTimeField(
        "Asignado en",
        auto_now_add=True,
    )
    is_active = models.BooleanField(
        "Activo",
        default=True,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="assignments",
    )
    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        verbose_name="Personal",
        related_name="truck_cycle_assignments",
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Asignado por",
        related_name="truck_cycle_assignments_made",
    )

    class Meta:
        db_table = "truck_cycle_assignment"
        verbose_name = "Asignación de Pauta"
        verbose_name_plural = "Asignaciones de Pauta"

    def __str__(self):
        return f"{self.get_role_display()} - Pauta {self.pauta_id}"


class PautaTimestampModel(models.Model):
    """Marcas de tiempo de eventos del ciclo"""

    EVENT_TYPE_CHOICES = [
        ('T0_PICKING_START', 'T0 - Inicio de Picking'),
        ('T1_PICKING_END', 'T1 - Fin de Picking'),
        ('T1A_YARD_START', 'T1A - Inicio Movimiento a Bahía'),
        ('T1B_YARD_END', 'T1B - Fin Movimiento a Bahía'),
        ('T2_BAY_ASSIGNED', 'T2 - Andén Asignado'),
        ('T3_LOADING_START', 'T3 - Inicio de Carga'),
        ('T4_LOADING_END', 'T4 - Fin de Carga'),
        ('T5_COUNT_START', 'T5 - Inicio de Conteo'),
        ('T6_COUNT_END', 'T6 - Fin de Conteo'),
        ('T7_CHECKOUT_SECURITY', 'T7 - Checkout Seguridad'),
        ('T8_CHECKOUT_OPS', 'T8 - Checkout Operaciones'),
        ('T8A_YARD_RETURN_START', 'T8A - Inicio Movimiento Bahía→Estacionamiento'),
        ('T8B_YARD_RETURN_END', 'T8B - Fin Movimiento Bahía→Estacionamiento'),
        ('T9_DISPATCH', 'T9 - Despacho'),
        ('T9B_TRIP_START', 'T9B - Inicio de Viaje'),
        ('T10_ARRIVAL', 'T10 - Llegada'),
        ('T10A_RELOAD_REENTRY', 'T10A - Re-ingreso Recarga'),
        ('T11_RELOAD_QUEUE', 'T11 - Cola de Recarga'),
        ('T12_RETURN_START', 'T12 - Inicio de Devolución'),
        ('T13_RETURN_END', 'T13 - Fin de Devolución'),
        ('T14_AUDIT_START', 'T14 - Inicio de Auditoría'),
        ('T15_AUDIT_END', 'T15 - Fin de Auditoría'),
        ('T16_CLOSE', 'T16 - Cierre'),
        ('T17_CANCELLED', 'T17 - Cancelada'),
    ]

    event_type = models.CharField(
        "Tipo de Evento",
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
    )
    timestamp = models.DateTimeField(
        "Marca de Tiempo",
        auto_now_add=True,
    )
    notes = models.TextField(
        "Notas",
        blank=True,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="timestamps",
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Registrado por",
        related_name="truck_cycle_timestamps",
    )

    class Meta:
        db_table = "truck_cycle_timestamp"
        verbose_name = "Marca de Tiempo de Pauta"
        verbose_name_plural = "Marcas de Tiempo de Pauta"

    def __str__(self):
        return f"{self.get_event_type_display()} - Pauta {self.pauta_id}"


class PautaBayAssignmentModel(models.Model):
    """Asignación de andén a pauta"""

    assigned_at = models.DateTimeField(
        "Asignado en",
        auto_now_add=True,
    )
    released_at = models.DateTimeField(
        "Liberado en",
        null=True,
        blank=True,
    )
    pauta = models.OneToOneField(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="bay_assignment",
    )
    bay = models.ForeignKey(
        BayModel,
        on_delete=models.CASCADE,
        verbose_name="Andén",
        related_name="pauta_assignments",
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Asignado por",
        related_name="truck_cycle_bay_assignments",
    )

    class Meta:
        db_table = "truck_cycle_bay_assignment"
        verbose_name = "Asignación de Andén"
        verbose_name_plural = "Asignaciones de Andén"

    def __str__(self):
        return f"Andén {self.bay.code} - Pauta {self.pauta_id}"


class InconsistencyModel(BaseModel):
    """Inconsistencias encontradas durante el ciclo"""

    PHASE_CHOICES = [
        ('VERIFICATION', 'Verificación'),
        ('CHECKOUT', 'Checkout'),
        ('RETURN', 'Devolución'),
        ('AUDIT', 'Auditoría'),
    ]

    TYPE_CHOICES = [
        ('FALTANTE', 'Faltante'),
        ('SOBRANTE', 'Sobrante'),
        ('CRUCE', 'Cruce'),
        ('DANADO', 'Dañado'),
    ]

    phase = models.CharField(
        "Fase",
        max_length=20,
        choices=PHASE_CHOICES,
    )
    inconsistency_type = models.CharField(
        "Tipo de Inconsistencia",
        max_length=20,
        choices=TYPE_CHOICES,
    )
    material_code = models.CharField(
        "Código de Material",
        max_length=20,
    )
    product_name = models.CharField(
        "Nombre del Producto",
        max_length=200,
        blank=True,
    )
    expected_quantity = models.PositiveIntegerField(
        "Cantidad Esperada",
        default=0,
    )
    actual_quantity = models.PositiveIntegerField(
        "Cantidad Real",
        default=0,
    )
    difference = models.IntegerField(
        "Diferencia",
        default=0,
    )
    notes = models.TextField(
        "Notas",
        blank=True,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="inconsistencies",
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Reportado por",
        related_name="truck_cycle_inconsistencies",
    )

    class Meta:
        db_table = "truck_cycle_inconsistency"
        verbose_name = "Inconsistencia"
        verbose_name_plural = "Inconsistencias"

    def __str__(self):
        return f"{self.get_inconsistency_type_display()} - {self.material_code}"


class PautaPhotoModel(BaseModel):
    """Fotos del ciclo del camión"""

    PHASE_CHOICES = [
        ('PRE_LOADING', 'Pre-Carga'),
        ('POST_LOADING', 'Post-Carga'),
        ('VERIFICATION', 'Verificación'),
        ('CHECKOUT', 'Checkout'),
        ('RETURN', 'Devolución'),
        ('AUDIT', 'Auditoría'),
    ]

    phase = models.CharField(
        "Fase",
        max_length=20,
        choices=PHASE_CHOICES,
    )
    photo = models.ImageField(
        "Foto",
        upload_to='truck_cycle/photos/',
    )
    description = models.CharField(
        "Descripción",
        max_length=200,
        blank=True,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="photos",
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Subido por",
        related_name="truck_cycle_photos",
    )

    class Meta:
        db_table = "truck_cycle_photo"
        verbose_name = "Foto de Pauta"
        verbose_name_plural = "Fotos de Pauta"

    def __str__(self):
        return f"{self.get_phase_display()} - Pauta {self.pauta_id}"


class CheckoutValidationModel(models.Model):
    """Validación de checkout"""

    security_validated = models.BooleanField(
        "Validado por Seguridad",
        default=False,
    )
    security_validated_at = models.DateTimeField(
        "Validado por Seguridad en",
        null=True,
        blank=True,
    )
    ops_validated = models.BooleanField(
        "Validado por Operaciones",
        default=False,
    )
    ops_validated_at = models.DateTimeField(
        "Validado por Operaciones en",
        null=True,
        blank=True,
    )
    exit_pass_consumables = models.BooleanField(
        "Pase de Salida de Consumibles",
        default=False,
    )
    dispatched_without_security = models.BooleanField(
        "Despachado sin Validación de Seguridad",
        default=False,
    )
    notes = models.TextField(
        "Notas",
        blank=True,
    )
    pauta = models.OneToOneField(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="checkout_validation",
    )
    security_validator = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Validador de Seguridad",
        related_name="security_validations",
    )
    ops_validator = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Validador de Operaciones",
        related_name="ops_validations",
    )

    class Meta:
        db_table = "truck_cycle_checkout"
        verbose_name = "Validación de Checkout"
        verbose_name_plural = "Validaciones de Checkout"

    def __str__(self):
        return f"Checkout - Pauta {self.pauta_id}"


class PalletTicketModel(BaseModel):
    """Tickets de tarima con QR"""

    ticket_number = models.CharField(
        "Número de Ticket",
        max_length=20,
    )
    qr_code = models.CharField(
        "Código QR",
        max_length=100,
        unique=True,
    )
    is_full_pallet = models.BooleanField(
        "Tarima Completa",
        default=True,
    )
    box_count = models.PositiveIntegerField(
        "Cantidad de Cajas",
        default=0,
    )
    scanned = models.BooleanField(
        "Escaneado",
        default=False,
    )
    scanned_at = models.DateTimeField(
        "Escaneado en",
        null=True,
        blank=True,
    )
    pauta = models.ForeignKey(
        PautaModel,
        on_delete=models.CASCADE,
        verbose_name="Pauta",
        related_name="pallet_tickets",
    )

    class Meta:
        db_table = "truck_cycle_pallet_ticket"
        verbose_name = "Ticket de Tarima"
        verbose_name_plural = "Tickets de Tarima"

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.qr_code}"
