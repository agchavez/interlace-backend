"""
Signals para el módulo personnel
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from datetime import date

from .models.certification import Certification
from .models.personnel import PersonnelProfile


@receiver(pre_save, sender=Certification)
def check_certification_expiration(sender, instance, **kwargs):
    """
    Actualizar is_valid basado en fecha de expiración
    """
    if instance.expiration_date < date.today():
        instance.is_valid = False


@receiver(post_save, sender=Certification)
def send_expiration_notification(sender, instance, created, **kwargs):
    """
    Enviar notificación si la certificación está por vencer o ha vencido

    Se envía notificación por correo electrónico en los siguientes casos:
    - Certificación próxima a vencer (dentro de 30 días)
    - Certificación recién vencida
    """
    from .utils.email_service import PersonnelEmailService

    if not created:
        return

    days_until_expiration = instance.days_until_expiration

    # Caso 1: Certificación próxima a vencer (1-30 días)
    if days_until_expiration and 1 <= days_until_expiration <= 30:
        if not instance.renewal_notification_sent:
            # Enviar notificación por correo
            email_sent = PersonnelEmailService.send_certification_expiring_notification(instance)

            if email_sent:
                # Marcar notificación como enviada
                Certification.objects.filter(pk=instance.pk).update(
                    renewal_notification_sent=True,
                    renewal_notification_date=date.today()
                )

    # Caso 2: Certificación ya vencida (días negativos)
    elif days_until_expiration and days_until_expiration < 0:
        # Enviar notificación urgente de certificación vencida
        PersonnelEmailService.send_certification_expired_notification(instance)
