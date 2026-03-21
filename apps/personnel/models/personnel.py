"""
Modelos principales de personal
"""
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class PersonnelProfile(models.Model):
    """
    Perfil completo del personal - ScoreCard

    IMPORTANTE: No todo el personal tiene usuario en el sistema.
    Muchos operativos solo tienen un registro/perfil pero NO acceso a la plataforma.
    El supervisor solicita tokens a nombre de ellos.
    """
    # Jerarquía de 4 niveles
    OPERATIVE = 'OPERATIVE'  # Picker, Contador, OPM
    SUPERVISOR = 'SUPERVISOR'
    AREA_MANAGER = 'AREA_MANAGER'  # Jefe de Área
    CD_MANAGER = 'CD_MANAGER'  # Gerente de Centro de Distribución

    HIERARCHY_LEVEL_CHOICES = [
        (OPERATIVE, 'Operativo (Picker/Contador/OPM)'),
        (SUPERVISOR, 'Supervisor'),
        (AREA_MANAGER, 'Jefe de Área'),
        (CD_MANAGER, 'Gerente de Centro de Distribución'),
    ]

    # Tipos de posición operativa
    PICKER = 'PICKER'
    COUNTER = 'COUNTER'
    OPM = 'OPM'
    YARD_DRIVER = 'YARD_DRIVER'
    LOADER = 'LOADER'
    WAREHOUSE_ASSISTANT = 'WAREHOUSE_ASSISTANT'
    SECURITY_GUARD = 'SECURITY_GUARD'
    DELIVERY_DRIVER = 'DELIVERY_DRIVER'
    ADMINISTRATIVE = 'ADMINISTRATIVE'
    OTHER = 'OTHER'

    POSITION_TYPE_CHOICES = [
        (PICKER, 'Picker'),
        (COUNTER, 'Contador'),
        (OPM, 'Operador de Montacargas'),
        (YARD_DRIVER, 'Conductor de Patio'),
        (LOADER, 'Cargador'),
        (WAREHOUSE_ASSISTANT, 'Ayudante de Almacén'),
        (SECURITY_GUARD, 'Guardia de Seguridad'),
        (DELIVERY_DRIVER, 'Conductor de Delivery'),
        (ADMINISTRATIVE, 'Administrativo'),
        (OTHER, 'Otro'),
    ]

    # Relación con usuario (OPCIONAL - puede ser NULL)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='personnel_profile',
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario del sistema (solo para personal con acceso a la plataforma)'
    )

    # Información básica (campos propios, NO dependen de user)
    employee_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[MinLengthValidator(3)],
        verbose_name='Código de empleado',
        help_text='Código único del empleado (ej: 22144, SUP001, OPM042)'
    )

    first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nombres'
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name='Apellidos'
    )

    email = models.EmailField(
        blank=True,
        verbose_name='Email',
        help_text='Email de contacto (no necesariamente tiene usuario en sistema)'
    )

    # Estructura organizacional
    primary_distributor_center = models.ForeignKey(
        'maintenance.DistributorCenter',
        on_delete=models.PROTECT,
        related_name='primary_personnel',
        verbose_name='Centro de distribución principal',
        help_text='Centro de distribución principal al que pertenece el empleado',
        db_column='distributor_center_id',  # Usar la misma columna que antes para preservar datos
        null=True,  # Temporal para migración
        blank=True
    )
    distributor_centers = models.ManyToManyField(
        'maintenance.DistributorCenter',
        related_name='all_personnel',
        verbose_name='Centros de distribución',
        blank=True,
        help_text='Todos los centros de distribución donde puede trabajar el empleado'
    )
    area = models.ForeignKey(
        'personnel.Area',
        on_delete=models.PROTECT,
        related_name='personnel',
        verbose_name='Área de negocio'
    )
    department = models.ForeignKey(
        'personnel.Department',
        on_delete=models.PROTECT,
        related_name='personnel',
        verbose_name='Departamento',
        null=True,
        blank=True
    )

    # Jerarquía y posición
    hierarchy_level = models.CharField(
        max_length=20,
        choices=HIERARCHY_LEVEL_CHOICES,
        default=OPERATIVE,
        verbose_name='Nivel jerárquico',
        db_index=True
    )
    position = models.CharField(
        max_length=100,
        verbose_name='Puesto actual',
        help_text='Título del puesto (ej: Supervisor de Turno Noche)'
    )
    position_type = models.CharField(
        max_length=30,
        choices=POSITION_TYPE_CHOICES,
        verbose_name='Tipo de posición',
        help_text='Categoría general del puesto'
    )

    # Supervisor inmediato (jerarquía)
    immediate_supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_personnel',
        verbose_name='Supervisor inmediato',
        limit_choices_to={'hierarchy_level__in': [SUPERVISOR, AREA_MANAGER, CD_MANAGER]}
    )

    # Datos laborales
    hire_date = models.DateField(
        verbose_name='Fecha de ingreso'
    )
    contract_type = models.CharField(
        max_length=50,
        choices=[
            ('PERMANENT', 'Permanente'),
            ('TEMPORARY', 'Temporal'),
            ('CONTRACT', 'Contrato'),
        ],
        default='PERMANENT',
        verbose_name='Tipo de contrato'
    )

    # Información personal
    personal_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Número de identidad',
        validators=[MinLengthValidator(13)]
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de nacimiento'
    )
    gender = models.CharField(
        max_length=10,
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('OTHER', 'Otro'),
        ],
        blank=True,
        verbose_name='Género'
    )
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('SINGLE', 'Soltero/a'),
            ('MARRIED', 'Casado/a'),
            ('DIVORCED', 'Divorciado/a'),
            ('WIDOWED', 'Viudo/a'),
            ('UNION', 'Unión libre'),
        ],
        blank=True,
        verbose_name='Estado civil'
    )

    # Contacto
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message='Número de teléfono inválido'
            )
        ],
        verbose_name='Teléfono'
    )
    personal_email = models.EmailField(
        blank=True,
        verbose_name='Email personal'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Dirección residencial'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad'
    )

    # Tallas de uniformes y EPP
    shirt_size = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Talla de camisa'
    )
    pants_size = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Talla de pantalón',
        help_text='Ej: 32, 34, 36'
    )
    shoe_size = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Talla de zapatos',
        help_text='Ej: 8, 9, 10'
    )
    glove_size = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Talla de guantes'
    )
    helmet_size = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Talla de casco'
    )

    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        db_index=True
    )
    termination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de terminación'
    )
    termination_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de terminación'
    )

    # Notas
    notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales'
    )

    # Foto de perfil
    photo = models.ImageField(
        upload_to='personnel/photos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Foto de perfil',
        help_text='Foto del empleado (formato: JPG, PNG, máx 5MB)'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='personnel_created',
        verbose_name='Creado por'
    )

    class Meta:
        db_table = 'app_personnel_profile'
        verbose_name = 'Perfil de Personal'
        verbose_name_plural = 'Perfiles de Personal'
        ordering = ['-is_active', 'first_name', 'last_name']
        indexes = [
            models.Index(fields=['employee_code']),
            models.Index(fields=['hierarchy_level']),
            models.Index(fields=['is_active']),
            models.Index(fields=['primary_distributor_center', 'is_active']),
            models.Index(fields=['area', 'is_active']),
        ]
        permissions = [
            ('view_all_personnel', 'Puede ver todo el personal'),
            ('manage_personnel', 'Puede gestionar personal'),
            ('view_sensitive_data', 'Puede ver datos sensibles'),
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"

    def save(self, *args, **kwargs):
        """
        Sobrescribe save para asegurar que el centro principal
        siempre esté en la lista de centros
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Después del save inicial, agregar el centro principal a la lista
        if self.primary_distributor_center:
            self.distributor_centers.add(self.primary_distributor_center)

    @property
    def full_name(self):
        """Nombre completo del empleado"""
        return f"{self.first_name} {self.last_name}"

    @property
    def has_system_access(self):
        """Indica si el empleado tiene acceso al sistema"""
        return self.user is not None

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def years_of_service(self):
        if not self.hire_date:
            return 0
        from datetime import date
        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )

    @property
    def has_valid_certifications(self):
        """Verifica si todas las certificaciones están vigentes"""
        return not self.certifications.filter(
            is_valid=False
        ).exists()

    @property
    def certifications_expiring_soon(self):
        """Certificaciones que vencen en los próximos 30 días"""
        from datetime import date, timedelta
        threshold = date.today() + timedelta(days=30)
        return self.certifications.filter(
            expiration_date__lte=threshold,
            expiration_date__gte=date.today(),
            is_valid=True
        )

    def can_approve_tokens_level_1(self):
        """Puede aprobar tokens de nivel 1"""
        return self.hierarchy_level in [
            self.SUPERVISOR,
            self.AREA_MANAGER,
            self.CD_MANAGER
        ]

    def can_approve_tokens_level_2(self):
        """Puede aprobar tokens de nivel 2"""
        return self.hierarchy_level in [
            self.AREA_MANAGER,
            self.CD_MANAGER
        ]

    def can_approve_tokens_level_3(self):
        """Puede aprobar tokens de nivel 3"""
        return self.hierarchy_level == self.CD_MANAGER

    @property
    def has_system_access(self):
        """
        Verifica si el personal tiene usuario activo en el sistema.
        No todo el personal tiene usuario - muchos operativos solo tienen perfil.
        """
        return self.user is not None and self.user.is_active

    def can_request_tokens(self):
        """
        Verifica si puede crear solicitudes de tokens.
        Solo personal con usuario y nivel supervisor+ pueden solicitar.
        """
        return self.has_system_access and self.can_approve_tokens_level_1()

    def can_validate_tokens(self):
        """
        Verifica si puede validar tokens (Personal de Seguridad).
        Solo el personal del área de Seguridad puede validar tokens en portería.
        """
        return (
            self.has_system_access and
            self.area is not None and
            self.area.code == 'SECURITY'
        )

    def get_supervised_personnel(self):
        """Retorna el personal que supervisa directamente"""
        return PersonnelProfile.objects.filter(
            immediate_supervisor=self,
            is_active=True
        )

    def get_all_subordinates(self):
        """Retorna todo el personal bajo su mando (recursivo)"""
        subordinates = list(self.get_supervised_personnel())
        for person in list(subordinates):
            subordinates.extend(person.get_all_subordinates())
        return subordinates


class EmergencyContact(models.Model):
    """
    Contactos de emergencia del personal
    """
    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name='emergency_contacts',
        verbose_name='Personal'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre completo'
    )
    relationship = models.CharField(
        max_length=50,
        choices=[
            ('SPOUSE', 'Cónyuge'),
            ('PARENT', 'Padre/Madre'),
            ('SIBLING', 'Hermano/a'),
            ('CHILD', 'Hijo/a'),
            ('FRIEND', 'Amigo/a'),
            ('OTHER', 'Otro'),
        ],
        verbose_name='Relación'
    )
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message='Número de teléfono inválido'
            )
        ],
        verbose_name='Teléfono principal'
    )
    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message='Número de teléfono inválido'
            )
        ],
        verbose_name='Teléfono alternativo'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Contacto principal'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_personnel_emergency_contact'
        verbose_name = 'Contacto de Emergencia'
        verbose_name_plural = 'Contactos de Emergencia'
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()}) - {self.personnel.employee_code}"
