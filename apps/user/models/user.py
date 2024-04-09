from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password


from rest_framework.exceptions import ValidationError
from apps.maintenance.models.distributor_center import DistributorCenter

class DetailGroup(models.Model):
    requiered_access = models.BooleanField(
        _('requiere access'),
        default=False,
        help_text=_(
            'requiere que se le asigne el acceso a los usuarios'
        ),
    )
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        verbose_name=_('group'),
        related_name='detail_group',
        null=True,
        blank=True
    )
    class Meta:
        db_table = "auth_group_detail"

class UserModel(AbstractUser):
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
        db_table = "auth_user"

    first_name = models.CharField(
        'first name',
        max_length=60,
        error_messages={
            'required': 'El nombre es es obligatorio',
            'max_length': 'El nombre debe tener menos de 60 caracteres'
        }
    )
    last_name = models.CharField(
        'last name',
        max_length=60,
        error_messages={
            'required': 'El apellido es obligatorio',
            'max_length': 'El apellido debe tener menos de 60 caracteres'
        }
    )
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'required': 'El email es obligatorio',
            'unique': 'El email ya existe'
        }
    )

    centro_distribucion = models.ForeignKey(
        DistributorCenter,
        # si se elimina el centro de distribución, el usuario queda null
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('centro de distribución'),
        related_name='user_centro_distribucion'
    )

    # centros de distribucion a los que tiene acceso el usuario


    # Numero de empleado valor numerico, unico pero opcional
    employee_number = models.IntegerField(
        _('numero de empleado'),
        unique=True,
        null=True,
        blank=True,
        error_messages={
            'unique': 'El numero de empleado ya existe, debe ser unico'
        }
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    def deactivate(self):
        self.is_active = False
        self.save()

    def activate(self):
        self.is_active = True
        self.save()

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    # Crear super usuario
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValidationError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValidationError('Superuser must have is_staff=True.')
        if extra_fields.get('is_active') is not True:
            raise ValidationError('Superuser must have is_active=True.')

        return self._create_user(email, password, **extra_fields)

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.upper()
        self.last_name = self.last_name.upper()
        # Contraseña se encripta solo si se esta creando un usuario o si se esta actualizando y la contraseña cambio
        if not self.pk or self.password != self.__class__.objects.get(pk=self.pk).password:
            self.password = make_password(self.password)

        return super(UserModel, self).save(*args, **kwargs)