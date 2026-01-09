"""
Script de diagnóstico para verificar la configuración PWA
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("DIAGNOSTICO DE CONFIGURACION PWA")
print("=" * 60)

# 1. Verificar VAPID keys
print("\n1. Verificando VAPID Keys:")
print(f"   VAPID_PRIVATE_KEY: {'✓ Configurada' if settings.VAPID_PRIVATE_KEY else '✗ NO configurada'}")
print(f"   VAPID_PUBLIC_KEY: {'✓ Configurada' if settings.VAPID_PUBLIC_KEY else '✗ NO configurada'}")
print(f"   VAPID_ADMIN_EMAIL: {settings.VAPID_ADMIN_EMAIL}")

if settings.VAPID_PUBLIC_KEY:
    print(f"\n   Clave pública (primeros 30 chars): {settings.VAPID_PUBLIC_KEY[:30]}...")

# 2. Verificar pywebpush
print("\n2. Verificando pywebpush:")
try:
    from pywebpush import webpush
    print("   ✓ pywebpush instalado correctamente")
except ImportError as e:
    print(f"   ✗ Error: {e}")

# 3. Verificar modelo PushSubscription
print("\n3. Verificando modelo PushSubscription:")
try:
    from apps.user.models import PushSubscription
    count = PushSubscription.objects.count()
    active_count = PushSubscription.objects.filter(is_active=True).count()
    print(f"   Total de suscripciones: {count}")
    print(f"   Suscripciones activas: {active_count}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 4. Verificar endpoint API
print("\n4. Endpoints API disponibles:")
print("   POST /api/push/subscribe/")
print("   POST /api/push/unsubscribe/")

# 5. Resumen
print("\n" + "=" * 60)
if settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY:
    print("✓ Configuración PWA completa")
    print("\nClave pública para frontend (.env):")
    print(f"VITE_VAPID_PUBLIC_KEY={settings.VAPID_PUBLIC_KEY}")
else:
    print("✗ Configuración PWA incompleta")
    print("\nEjecuta: python generate_vapid.py")
print("=" * 60)
