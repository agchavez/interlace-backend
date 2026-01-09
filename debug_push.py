"""
Script de diagnóstico para push notifications
Ejecutar: python debug_push.py <user_id>
"""
import os
import sys
import json
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from apps.user.models import PushSubscription
from apps.user.models import UserModel

def diagnose_push(user_id):
    print("=" * 70)
    print("DIAGNÓSTICO DE PUSH NOTIFICATIONS")
    print("=" * 70)

    # 1. Verificar configuración VAPID
    print("\n[1] CONFIGURACIÓN VAPID")
    print("-" * 40)
    vapid_public = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    vapid_email = getattr(settings, 'VAPID_ADMIN_EMAIL', None)

    print(f"VAPID_PUBLIC_KEY: {vapid_public[:50] if vapid_public else 'NO CONFIGURADA'}...")
    print(f"VAPID_PRIVATE_KEY: {'[OK] Configurada' if vapid_private else '[X] NO CONFIGURADA'}")
    print(f"VAPID_ADMIN_EMAIL: {vapid_email or 'NO CONFIGURADO'}")

    # 2. Verificar usuario
    print(f"\n[2] USUARIO (ID: {user_id})")
    print("-" * 40)
    try:
        user = UserModel.objects.get(id=user_id)
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Activo: {user.is_active}")
    except UserModel.DoesNotExist:
        print(f"ERROR: Usuario con ID {user_id} no existe")
        return

    # 3. Verificar suscripciones
    print(f"\n[3] SUSCRIPCIONES PUSH")
    print("-" * 40)
    subscriptions = PushSubscription.objects.filter(user=user)
    print(f"Total suscripciones: {subscriptions.count()}")
    print(f"Activas: {subscriptions.filter(is_active=True).count()}")
    print(f"Inactivas: {subscriptions.filter(is_active=False).count()}")

    for idx, sub in enumerate(subscriptions.filter(is_active=True), 1):
        print(f"\n  Suscripción #{idx} (ID: {sub.id})")
        print(f"  Endpoint: {sub.endpoint}")
        print(f"  Auth (len): {len(sub.auth) if sub.auth else 0}")
        print(f"  P256dh (len): {len(sub.p256dh) if sub.p256dh else 0}")
        print(f"  Creada: {sub.created_at}")
        print(f"  Actualizada: {sub.updated_at}")

        # Detectar origen por endpoint
        if 'fcm.googleapis.com' in sub.endpoint:
            print(f"  Push Service: Google FCM (Chrome)")
        elif 'mozilla.com' in sub.endpoint or 'push.services.mozilla.com' in sub.endpoint:
            print(f"  Push Service: Mozilla (Firefox)")
        elif 'windows.com' in sub.endpoint or 'notify.windows.com' in sub.endpoint:
            print(f"  Push Service: Microsoft (Edge)")
        elif 'apple.com' in sub.endpoint:
            print(f"  Push Service: Apple (Safari)")
        else:
            print(f"  Push Service: Desconocido")

    # 4. Intentar enviar push con logging detallado
    print(f"\n[4] PRUEBA DE ENVÍO")
    print("-" * 40)

    try:
        from pywebpush import webpush, WebPushException
        from py_vapid import Vapid
        print("[OK] pywebpush y py_vapid importados correctamente")
    except ImportError as e:
        print(f"[X] Error importando librerías: {e}")
        return

    active_subs = subscriptions.filter(is_active=True)
    if not active_subs.exists():
        print("No hay suscripciones activas para probar")
        return

    for sub in active_subs:
        print(f"\n  Enviando a suscripción {sub.id}...")

        payload = {
            "notification": {
                "title": "Test de diagnóstico",
                "body": "Si ves esto, las push notifications funcionan!",
            }
        }

        vapid_claims = {
            "sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"
        }

        try:
            vapid = Vapid.from_pem(settings.VAPID_PRIVATE_KEY.encode('utf-8'))

            response = webpush(
                subscription_info=sub.subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid,
                vapid_claims=vapid_claims
            )

            print(f"  [OK] ÉXITO!")
            print(f"    Status: {response.status_code if hasattr(response, 'status_code') else 'OK'}")

        except WebPushException as e:
            print(f"  [X] ERROR WebPush:")
            print(f"    Mensaje: {e}")
            if e.response:
                print(f"    Status Code: {e.response.status_code}")
                print(f"    Response: {e.response.text[:200] if e.response.text else 'Sin respuesta'}")

                if e.response.status_code == 401:
                    print("    -> CAUSA: Error de autenticación VAPID. Las keys no coinciden.")
                elif e.response.status_code == 403:
                    print("    -> CAUSA: Acceso prohibido. Verifica VAPID claims.")
                elif e.response.status_code == 404:
                    print("    -> CAUSA: Suscripción no encontrada. El usuario se desuscribió.")
                elif e.response.status_code == 410:
                    print("    -> CAUSA: Suscripción expirada. Debe re-suscribirse.")

        except Exception as e:
            print(f"  [X] ERROR inesperado: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python debug_push.py <user_id>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    diagnose_push(user_id)
