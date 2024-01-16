from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def create_mail(user_mail, subject, template_name, context):
    try:
        content = render_to_string(template_name, context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=content,
            from_email='Plataforma Tracker <' + settings.EMAIL_HOST_USER + '>',
            to=[
                user_mail
            ],
        )

        message.attach_alternative(content, 'text/html')
        message.send(fail_silently=False)
        return True, 'Se envio el correo de %s a %s' % (subject, user_mail)
    except Exception as e:
        print(e)
        return False, 'No se pudo enviar el correo de %s a %s' % (subject, user_mail)
