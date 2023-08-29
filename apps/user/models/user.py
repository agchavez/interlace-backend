from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
import uuid

from rest_framework.exceptions import ValidationError


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
        related_name='detail_group'
    )
    class Meta:
        db_table = "auth_group_detail"

class UserModel(AbstractUser):
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
        db_table = "auth_user"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.upper()
        self.last_name = self.last_name.upper()
        self.password = make_password(self.password)
        return super().save(*args, **kwargs)

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

class UserManager(BaseUserManager):

    def create_user(self, email, password=None):

        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password):

        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user