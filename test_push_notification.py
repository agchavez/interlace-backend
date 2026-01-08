"""
Script para probar notificaciones push
Ejecuta: python test_push_notification.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.user.models import UserModel
from apps.user.utils.push_notifications import send_push_to_user

def test_notification():
    """Envía una notificación de prueba al usuario con id=3"""

    # Obtener el usuario
    try:
        user = UserModel.objects.get(id=3)
        print(f"[OK] Usuario encontrado: {user.username} ({user.first_name} {user.last_name})")
    except UserModel.DoesNotExist:
        print("[ERROR] Usuario con id=3 no existe")
        return

    # Verificar suscripciones
    from apps.user.models import PushSubscription
    subs = PushSubscription.objects.filter(user=user, is_active=True)
    print(f"[INFO] Suscripciones activas: {subs.count()}")

    if subs.count() == 0:
        print("[ERROR] El usuario no tiene suscripciones activas")
        return

    # Enviar notificación
    print("\n[SENDING] Enviando notificacion de prueba...")

    sent_count = send_push_to_user(
        user=user,
        title="Notificacion de Prueba!",
        body="Tu sistema de notificaciones push esta funcionando correctamente",
        icon="/icons/icon-192x192.png",
        data={
            "url": "/",
            "type": "test"
        }
    )

    if sent_count > 0:
        print(f"[SUCCESS] Notificacion enviada exitosamente! ({sent_count} enviada(s))")
        print("\n[INFO] Deberias recibir la notificacion en tu navegador en 2-3 segundos")
    else:
        print("[ERROR] Error al enviar la notificacion. Revisa los logs.")

if __name__ == "__main__":
    test_notification()
