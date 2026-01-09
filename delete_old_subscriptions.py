"""
Elimina las suscripciones push antiguas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.user.models import PushSubscription

# Eliminar todas las suscripciones
count = PushSubscription.objects.all().count()
PushSubscription.objects.all().delete()

print(f"[OK] {count} suscripciones eliminadas")
print("[INFO] Ahora necesitas volver a suscribirte desde el navegador con las nuevas claves VAPID")
