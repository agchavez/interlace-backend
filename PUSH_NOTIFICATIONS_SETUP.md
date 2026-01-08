# Configuración Push Notifications - Backend

## ✅ Checklist de Configuración

### 1. Archivo de Clave Privada VAPID

**Ubicación**: `vapid_private.pem` en la raíz del proyecto (mismo nivel que `manage.py`)

```bash
# Debe contener:
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg0ycETnxWL8NWpryc
j94IMgoPoFge3r1UM5mt2lQxi4ShRANCAATHaNdZQFvogKznwetnbrSRFbvYvraG
8KeyWExblg1Cs5kK3E+6YQfVe0LntY67EB45QtTldNzbghiJxq6Sw8fl
-----END PRIVATE KEY-----
```

**IMPORTANTE**: No commitear este archivo al repositorio. Agregarlo a `.gitignore`.

### 2. Variables de Entorno

Agregar a `.env`:

```bash
# Push Notifications
VAPID_PUBLIC_KEY=BKo2jXWUBb6ICs58HrZ260kRW72L62hvCnslhMW5YNQrOZCtxPumEH1XtC57WOuxAeOULU5XTc24IYicaukvPH5
VAPID_ADMIN_EMAIL=admin@tudominio.com
```

**CRÍTICO**: La `VAPID_PUBLIC_KEY` debe ser la misma que se configuró en el frontend (`VITE_VAPID_PUBLIC_KEY`).

### 3. Dependencias Python

```bash
pip install pywebpush py-vapid
```

O agregar a `requirements.txt`:
```txt
pywebpush==1.14.0
py-vapid==1.9.0
```

### 4. Verificar Configuración en `settings.py`

El código ya está agregado en `config/settings.py`:

```python
# Web Push Notifications - VAPID Configuration
VAPID_PRIVATE_KEY_FILE = os.path.join(BASE_DIR, 'vapid_private.pem')
if os.path.exists(VAPID_PRIVATE_KEY_FILE):
    with open(VAPID_PRIVATE_KEY_FILE, 'r') as f:
        VAPID_PRIVATE_KEY = f.read().strip()
else:
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '').replace('\\n', '\n')

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_ADMIN_EMAIL = os.getenv('VAPID_ADMIN_EMAIL', 'admin@example.com')
```

### 5. Código de Envío

El código ya está en `apps/user/utils/push_notifications.py`:

```python
from py_vapid import Vapid
from pywebpush import webpush, WebPushException
import json
from django.conf import settings
import os

def send_push_notification(subscription, title, body, data=None):
    """
    Envía una push notification a una suscripción específica
    """
    payload = {
        'notification': {
            'title': title,
            'body': body,
            'icon': '/icons/icon-192x192.png',
            'badge': '/icons/icon-96x96.png',
            'tag': 'tracker-notification',
            'data': data or {}
        }
    }

    vapid_key_path = os.path.join(settings.BASE_DIR, 'vapid_private.pem')

    vapid_claims = {
        'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'
    }

    try:
        vapid = Vapid.from_file(vapid_key_path)

        response = webpush(
            subscription_info=subscription.subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid,
            vapid_claims=vapid_claims
        )

        print(f"✓ Push notification enviada: {response.status_code}")
        return True

    except WebPushException as ex:
        print(f"✗ Error enviando push: {ex}")
        if ex.response and ex.response.status_code == 410:
            # Suscripción expirada, eliminarla
            subscription.delete()
        return False
```

## 🧪 Probar Push Notifications

Usar el script `test_push_notification.py`:

```bash
python test_push_notification.py
```

El script:
1. Busca suscripciones activas en la base de datos
2. Envía una notificación de prueba
3. Muestra el resultado

## 🚀 Despliegue en Producción

### Docker

Si usas Docker, asegúrate de:

1. **Copiar `vapid_private.pem` al contenedor**:
   ```dockerfile
   COPY vapid_private.pem /app/vapid_private.pem
   ```

2. **Variables de entorno en `docker-compose.yml`**:
   ```yaml
   environment:
     - VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY}
     - VAPID_ADMIN_EMAIL=${VAPID_ADMIN_EMAIL}
   ```

3. **O montarlo como secret** (más seguro):
   ```yaml
   secrets:
     - vapid_private_key

   secrets:
     vapid_private_key:
       file: ./vapid_private.pem
   ```

### Dokploy / Servidor

1. **Copiar archivo al servidor**:
   ```bash
   scp vapid_private.pem usuario@servidor:/ruta/al/proyecto/
   ```

2. **Configurar variables de entorno** en el panel de Dokploy

3. **Reiniciar el backend** para aplicar cambios

## 🔐 Seguridad

### ❌ NO HACER:
- Commitear `vapid_private.pem` al repositorio
- Exponer la clave privada en logs o respuestas API
- Usar la misma clave en múltiples proyectos

### ✅ SÍ HACER:
- Agregar `vapid_private.pem` a `.gitignore`
- Usar variables de entorno para la clave pública
- Rotar claves periódicamente (cada 6-12 meses)
- Usar HTTPS siempre

## 🐛 Troubleshooting

### Error: "VAPID dict missing 'private_key'"
- Verificar que `vapid_private.pem` existe en la raíz del proyecto
- Verificar permisos del archivo (debe ser legible por el proceso)

### Error: "Could not deserialize key data"
- El archivo debe estar en formato PEM válido
- Debe empezar con `-----BEGIN PRIVATE KEY-----`
- Debe terminar con `-----END PRIVATE KEY-----`
- Sin líneas vacías al principio o final

### Error: "Subscription has expired"
- El usuario debe suscribirse de nuevo desde el frontend
- La suscripción se eliminará automáticamente de la BD

### Notificaciones no llegan
1. Verificar que la clave pública coincide entre frontend y backend
2. Verificar logs del backend al enviar
3. Verificar que el service worker está registrado en el navegador
4. Verificar permisos de notificaciones en el navegador

## 📊 Modelos de Base de Datos

El modelo `PushSubscription` ya está creado:

```python
class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    subscription_info = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

Campos en `subscription_info`:
- `endpoint`: URL del push service
- `keys.p256dh`: Clave pública del cliente
- `keys.auth`: Secret de autenticación

## 📝 Ejemplo de Uso en Código

```python
from apps.user.models import PushSubscription
from apps.user.utils.push_notifications import send_push_notification

# Obtener todas las suscripciones de un usuario
subscriptions = PushSubscription.objects.filter(user=request.user)

# Enviar notificación a todas
for sub in subscriptions:
    send_push_notification(
        subscription=sub,
        title='Nueva tarea asignada',
        body='Tienes una nueva tarea pendiente',
        data={'task_id': 123, 'url': '/tasks/123'}
    )
```

## 🎯 Integración con Signals

Para enviar notificaciones automáticamente cuando ocurre algo:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.user.utils.push_notifications import send_push_notification

@receiver(post_save, sender=Task)
def notify_task_assigned(sender, instance, created, **kwargs):
    if created and instance.assigned_to:
        # Obtener suscripciones del usuario asignado
        subscriptions = PushSubscription.objects.filter(user=instance.assigned_to)

        for sub in subscriptions:
            send_push_notification(
                subscription=sub,
                title='Nueva tarea asignada',
                body=f'Te han asignado: {instance.title}',
                data={'task_id': instance.id}
            )
```

---

**¿Dudas?** Revisar `test_push_notification.py` para ver un ejemplo completo de uso.
