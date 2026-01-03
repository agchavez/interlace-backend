"""
Servicio de envío de correos electrónicos para el módulo de personal
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import date
import logging

logger = logging.getLogger(__name__)


class PersonnelEmailService:
    """Servicio para enviar correos electrónicos relacionados con personal"""

    @staticmethod
    def send_certification_expiring_notification(certification):
        """
        Envía notificación de certificación próxima a vencer

        Args:
            certification: Instancia de Certification

        Returns:
            bool: True si el correo se envió correctamente, False en caso contrario
        """
        try:
            personnel = certification.personnel
            days_until_expiration = certification.days_until_expiration

            # Determinar el destinatario
            # Si el personal tiene usuario y email, enviar a su email
            # Si no, enviar al supervisor o al área de People/RRHH
            recipient_email = None
            recipient_name = personnel.full_name

            if personnel.user and personnel.user.email:
                recipient_email = personnel.user.email
            elif personnel.email:
                recipient_email = personnel.email
            elif personnel.immediate_supervisor and personnel.immediate_supervisor.user:
                recipient_email = personnel.immediate_supervisor.user.email
                recipient_name = personnel.immediate_supervisor.full_name
                logger.info(
                    f"Personal {personnel.employee_code} no tiene email. "
                    f"Enviando notificación al supervisor {recipient_name}"
                )

            if not recipient_email:
                logger.warning(
                    f"No se pudo determinar destinatario para notificación de "
                    f"certificación {certification.id} del personal {personnel.employee_code}"
                )
                return False

            # Contexto para el template
            context = {
                'certification': certification,
                'personnel': personnel,
                'days_until_expiration': days_until_expiration,
                'portal_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else '#',
                'current_year': date.today().year,
            }

            # Renderizar el template HTML
            html_content = render_to_string(
                'personnel/emails/certification_expiring.html',
                context
            )

            # Crear el email
            subject = f'⚠️ Certificación por Vencer - {certification.certification_type.name}'

            # Texto plano alternativo
            text_content = f"""
Estimado/a {personnel.full_name},

Le informamos que su certificación {certification.certification_type.name}
está próxima a vencer en {days_until_expiration} día(s).

Detalles de la Certificación:
- Número: {certification.certification_number}
- Fecha de Expiración: {certification.expiration_date.strftime('%d/%m/%Y')}
- Autoridad Emisora: {certification.issuing_authority}

Por favor, gestione su renovación lo antes posible.

Este es un mensaje automático del sistema ABInBev Tracker.

Saludos,
Sistema de Gestión de Personal
            """.strip()

            # Crear y enviar el correo
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[recipient_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(
                f"Notificación de certificación por vencer enviada a {recipient_email} "
                f"para certificación {certification.id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error al enviar notificación de certificación por vencer "
                f"para certificación {certification.id}: {str(e)}",
                exc_info=True
            )
            return False

    @staticmethod
    def send_certification_expired_notification(certification):
        """
        Envía notificación de certificación vencida

        Args:
            certification: Instancia de Certification

        Returns:
            bool: True si el correo se envió correctamente, False en caso contrario
        """
        try:
            personnel = certification.personnel

            # Determinar destinatarios (personal + supervisor + RRHH)
            recipients = []

            # Email del personal
            if personnel.user and personnel.user.email:
                recipients.append(personnel.user.email)
            elif personnel.email:
                recipients.append(personnel.email)

            # Email del supervisor (siempre notificar)
            if personnel.immediate_supervisor and personnel.immediate_supervisor.user:
                supervisor_email = personnel.immediate_supervisor.user.email
                if supervisor_email and supervisor_email not in recipients:
                    recipients.append(supervisor_email)

            # TODO: Agregar email del área de People/RRHH
            # Esto requeriría tener configurado un email para el área de RRHH

            if not recipients:
                logger.warning(
                    f"No se pudieron determinar destinatarios para notificación de "
                    f"certificación vencida {certification.id} del personal {personnel.employee_code}"
                )
                return False

            # Contexto para el template
            context = {
                'certification': certification,
                'personnel': personnel,
                'portal_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else '#',
                'current_year': date.today().year,
            }

            # Renderizar el template HTML
            html_content = render_to_string(
                'personnel/emails/certification_expired.html',
                context
            )

            # Crear el email
            subject = f'🚨 URGENTE: Certificación Vencida - {certification.certification_type.name}'

            # Texto plano alternativo
            text_content = f"""
ALERTA: CERTIFICACIÓN VENCIDA

Estimado/a {personnel.full_name},

Su certificación {certification.certification_type.name} ha VENCIDO
el día {certification.expiration_date.strftime('%d/%m/%Y')}.

Detalles de la Certificación:
- Número: {certification.certification_number}
- Estado: VENCIDA
- {'ES OBLIGATORIA' if certification.certification_type.is_mandatory else 'Renovación recomendada'}

ACCIÓN INMEDIATA REQUERIDA:
1. Contacte al departamento de People/RRHH
2. Inicie el proceso de renovación lo antes posible
3. Informe a su supervisor

Este es un mensaje automático del sistema ABInBev Tracker.

Saludos,
Sistema de Gestión de Personal
            """.strip()

            # Crear y enviar el correo
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=recipients,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(
                f"Notificación de certificación vencida enviada a {', '.join(recipients)} "
                f"para certificación {certification.id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error al enviar notificación de certificación vencida "
                f"para certificación {certification.id}: {str(e)}",
                exc_info=True
            )
            return False
