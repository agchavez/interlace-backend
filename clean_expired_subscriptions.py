"""
Script para limpiar suscripciones push expiradas de la base de datos
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.user.models import PushSubscription
from pywebpush import webpush, WebPushException
from py_vapid import Vapid
from django.conf import settings
import json

def test_subscription(subscription):
    """
    Prueba si una suscripción está activa enviando un payload vacío
    Retorna True si está activa, False si está expirada
    """
    vapid_key_path = os.path.join(settings.BASE_DIR, 'vapid_private.pem')
    vapid_claims = {
        'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'
    }

    try:
        vapid = Vapid.from_file(vapid_key_path)

        # Intentar enviar un payload mínimo
        response = webpush(
            subscription_info=subscription.subscription_info,
            data=json.dumps({'test': True}),
            vapid_private_key=vapid,
            vapid_claims=vapid_claims
        )

        return True

    except WebPushException as ex:
        if ex.response and ex.response.status_code == 410:
            # Suscripción expirada
            return False
        else:
            # Otro error - por seguridad asumimos que está activa
            print(f"  [!] Error inesperado: {ex}")
            return True

def main():
    print("=" * 60)
    print("🧹 LIMPIEZA DE SUSCRIPCIONES PUSH EXPIRADAS")
    print("=" * 60)
    print()

    # Obtener todas las suscripciones
    all_subscriptions = PushSubscription.objects.all()
    total_count = all_subscriptions.count()

    print(f"[INFO] Total de suscripciones en BD: {total_count}")
    print()

    if total_count == 0:
        print("[OK] No hay suscripciones en la base de datos")
        return

    # Agrupar por usuario
    users_subs = {}
    for sub in all_subscriptions:
        user_key = f"{sub.user.username} ({sub.user.get_full_name()})"
        if user_key not in users_subs:
            users_subs[user_key] = []
        users_subs[user_key].append(sub)

    print(f"[INFO] Usuarios con suscripciones: {len(users_subs)}")
    print()

    # Probar cada suscripción
    expired_count = 0
    active_count = 0

    for user_key, subs in users_subs.items():
        print(f"👤 Usuario: {user_key}")
        print(f"   Suscripciones: {len(subs)}")

        for idx, sub in enumerate(subs, 1):
            print(f"   [{idx}] Probando suscripción {sub.id}...", end=" ")

            is_active = test_subscription(sub)

            if is_active:
                print("✓ ACTIVA")
                active_count += 1
            else:
                print("✗ EXPIRADA (eliminando...)")
                sub.delete()
                expired_count += 1

        print()

    # Resumen
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"✓ Suscripciones activas: {active_count}")
    print(f"✗ Suscripciones expiradas eliminadas: {expired_count}")
    print()

    if expired_count > 0:
        print("💡 Los usuarios afectados deben volver a suscribirse desde el frontend")
    else:
        print("✓ Todas las suscripciones están activas")

if __name__ == '__main__':
    main()
