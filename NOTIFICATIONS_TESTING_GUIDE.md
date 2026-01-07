# 🔔 Guía de Pruebas - Sistema de Notificaciones en Tiempo Real

Esta guía explica cómo probar el sistema de notificaciones en tiempo real del proyecto Tracker.

## 📋 Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Requisitos Previos](#requisitos-previos)
3. [Métodos para Crear Notificaciones de Prueba](#métodos-para-crear-notificaciones-de-prueba)
4. [Tipos de Notificaciones Disponibles](#tipos-de-notificaciones-disponibles)
5. [WebSocket - Notificaciones en Tiempo Real](#websocket---notificaciones-en-tiempo-real)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🏗️ Arquitectura del Sistema

El sistema de notificaciones utiliza:

- **Django REST Framework** - API REST para gestión de notificaciones
- **Django Channels** - WebSocket para comunicación en tiempo real
- **Redis** - Channel layer para broadcasting
- **React + RTK Query** - Frontend para consumir notificaciones

### Flujo de Notificaciones

```
1. Evento → 2. Crear NotificationModel → 3. Guardar en DB → 4. WebSocket Broadcast → 5. Cliente React
```

---

## ✅ Requisitos Previos

Antes de comenzar, asegúrate de tener:

1. **Backend corriendo**: `python manage.py runserver`
2. **Redis corriendo**: `redis-server` (para WebSocket)
3. **Frontend corriendo**: `npm run dev` (en tracker-frontend)
4. **Usuario de prueba**: Conoce el ID del usuario (ejemplo: user_id=1)

### Verificar que Redis está corriendo

```bash
# Windows
redis-cli ping
# Debe responder: PONG

# Linux/Mac
redis-cli ping
```

---

## 🛠️ Métodos para Crear Notificaciones de Prueba

### Método 1: Management Command (Recomendado)

El management command permite crear múltiples notificaciones con variedad de tipos.

```bash
# Crear 1 notificación para el usuario 1
python manage.py create_test_notifications --user 1

# Crear 5 notificaciones variadas para el usuario 1
python manage.py create_test_notifications --user 1 --count 5 --variety

# Crear notificación de tipo ALERTA
python manage.py create_test_notifications --user 1 --type ALERTA

# Crear notificaciones para todos los usuarios activos
python manage.py create_test_notifications --all-users --count 2

# Ver ayuda completa
python manage.py create_test_notifications --help
```

**Ventajas:**
- ✅ Fácil de usar
- ✅ Incluye 13 plantillas predefinidas
- ✅ Envía notificaciones por WebSocket automáticamente
- ✅ Logs detallados en consola

---

### Método 2: Script Python

Script independiente que usa la API REST.

```bash
# Edita el script primero y configura USER_ID y TOKEN
# Archivo: scripts/create_notifications.py

# Ejecutar el script
python scripts/create_notifications.py
```

**Ventajas:**
- ✅ No requiere acceso directo a Django
- ✅ Usa la API REST (más realista)
- ✅ Fácil de personalizar
- ✅ Incluye 6 notificaciones de ejemplo

---

### Método 3: API REST - Endpoint de Prueba

Usa el endpoint `/api/notification/test/` directamente.

#### Usando cURL

```bash
# Notificación básica (GET)
curl "http://localhost:8000/api/notification/test/?user_id=1"

# Notificación personalizada (POST)
curl -X POST http://localhost:8000/api/notification/test/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "type": "ALERTA",
    "module": "TRACKER",
    "title": "Notificación de Prueba",
    "subtitle": "Esta es una prueba",
    "description": "Descripción completa de la notificación de prueba",
    "url": "/dashboard",
    "identifier": 123,
    "json_data": {
      "custom_field": "valor personalizado"
    }
  }'
```

#### Usando Postman/Insomnia

**Endpoint:** `POST http://localhost:8000/api/notification/test/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "user_id": 1,
  "type": "INFORMACION",
  "module": "TRACKER",
  "title": "Prueba desde Postman",
  "subtitle": "Subtítulo de la notificación",
  "description": "Esta es una descripción detallada de la notificación",
  "url": "/dashboard",
  "identifier": 456,
  "json_data": {
    "test": true,
    "source": "postman"
  },
  "html": "<p><strong>Contenido HTML</strong> opcional</p>"
}
```

---

### Método 4: Django Admin

También puedes crear notificaciones directamente desde el admin de Django.

1. Ve a: `http://localhost:8000/admin/`
2. Login con credenciales de superusuario
3. Busca "Notifications" en el panel lateral
4. Haz clic en "Add Notification"
5. Completa el formulario y guarda

**⚠️ Nota:** Las notificaciones creadas por admin NO se envían automáticamente por WebSocket.

---

### Método 5: Django Shell

Para pruebas más avanzadas o integración con otros procesos.

```bash
python manage.py shell
```

```python
from apps.user.models import UserModel, NotificationModel
from apps.user.serializers import NotificationSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Obtener usuario
user = UserModel.objects.get(id=1)

# Crear notificación
notification = NotificationModel.objects.create(
    user=user,
    type=NotificationModel.Type.ALERT,
    module=NotificationModel.Modules.TRACKER,
    title="Notificación desde Django Shell",
    subtitle="Prueba de notificación",
    description="Esta notificación fue creada desde el shell de Django",
    url="/dashboard",
    json={"test": True}
)

# Enviar por WebSocket
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    str(user.id),
    {
        'type': 'send_notification',
        'data': NotificationSerializer(notification).data
    }
)

print(f"✓ Notificación #{notification.id} creada y enviada")
```

---

## 📌 Tipos de Notificaciones Disponibles

### Tipos (Type)

| Tipo | Valor | Uso Recomendado |
|------|-------|-----------------|
| Ubicación | `UBICACION` | Rastreo de paquetes, tracking |
| Alerta | `ALERTA` | Situaciones urgentes que requieren atención |
| Recordatorio | `RECORDATORIO` | Eventos próximos, tareas pendientes |
| Tarea | `TAREA` | Asignación de nuevas tareas |
| Actualización | `ACTUALIZACION` | Cambios en datos o configuración |
| Advertencia | `ADVERTENCIA` | Situaciones que requieren precaución |
| Información | `INFORMACION` | Mensajes informativos generales |
| Error | `ERROR` | Errores del sistema o proceso |
| Registro | `REGISTRO` | Nuevos registros o usuarios |
| Aprobación | `APROBACION` | Solicitudes que requieren aprobación |
| Confirmación | `CONFIRMACION` | Confirmación de operaciones |
| Rechazo | `RECHAZO` | Solicitudes rechazadas |
| Reclamo | `RECLAMO` | Nuevos reclamos o quejas |

### Módulos (Module)

| Módulo | Valor | Descripción |
|--------|-------|-------------|
| T1 | `T1` | Módulo de tracking T1 |
| T2 | `T2` | Módulo de tracking T2 |
| Reclamo | `RECLAMO` | Sistema de reclamos |
| Tracker | `TRACKER` | Sistema de rastreo general |
| Usuario | `USUARIO` | Gestión de usuarios |
| Producto | `PRODUCTO` | Gestión de productos |
| Otros | `OTROS` | Otros módulos |

---

## 🔌 WebSocket - Notificaciones en Tiempo Real

### Conectarse al WebSocket

El frontend se conecta automáticamente al WebSocket cuando el usuario inicia sesión.

**URL del WebSocket:**
```
ws://localhost:8000/ws/notification/<user_id>/
```

**Ejemplo:** Para el usuario con ID 1:
```
ws://localhost:8000/ws/notification/1/
```

### Mensajes WebSocket

El WebSocket envía y recibe diferentes tipos de mensajes:

#### 1. Notificaciones Iniciales (al conectarse)

Al conectarse, el servidor envía todas las notificaciones no leídas:

```json
{
  "type": "data_notification",
  "data": [
    {
      "id": 1,
      "user": 1,
      "type": "ALERTA",
      "title": "Notificación de ejemplo",
      "subtitle": "Subtítulo",
      "description": "Descripción completa",
      "read": false,
      "created_at": "2026-01-07T12:00:00Z",
      ...
    }
  ]
}
```

#### 2. Nueva Notificación

Cuando se crea una nueva notificación:

```json
{
  "type": "new_notification",
  "data": {
    "id": 5,
    "user": 1,
    "type": "CONFIRMACION",
    "title": "Nueva notificación",
    ...
  }
}
```

#### 3. Notificación Marcada como Leída

Cuando se marca una notificación como leída:

```json
{
  "type": "notificacion_leida",
  "data": {
    "id": 5
  }
}
```

#### 4. Todas las Notificaciones Marcadas como Leídas

```json
{
  "type": "notificaciones_leidas"
}
```

---

## 🧪 Flujo de Prueba Completo

### Paso 1: Preparar el Entorno

```bash
# Terminal 1 - Redis
redis-server

# Terminal 2 - Backend Django
cd tracker-backend
python manage.py runserver

# Terminal 3 - Frontend React
cd tracker-frontend
npm run dev
```

### Paso 2: Iniciar Sesión en el Frontend

1. Abre `http://localhost:3000`
2. Inicia sesión con tu usuario (ID 1 en este ejemplo)
3. Observa el ícono de notificaciones en la barra superior (campana)

### Paso 3: Crear Notificaciones de Prueba

```bash
# Terminal 4 - Crear notificaciones
cd tracker-backend
python manage.py create_test_notifications --user 1 --count 5 --variety
```

### Paso 4: Verificar en el Frontend

1. **Icono de notificaciones**: Debe mostrar un badge con el número de no leídas
2. **Click en el icono**: Se abre el drawer con las notificaciones
3. **Click en una notificación**: Navega a la página de detalle
4. **Toast notification**: Debe aparecer un toast cuando llega una nueva notificación
5. **Sonido**: Debe reproducir un sonido de notificación

### Paso 5: Probar Funcionalidades

- ✅ Ver lista de notificaciones en el drawer
- ✅ Hacer clic en una notificación para marcarla como leída
- ✅ Ir a `/notifications` para ver la página completa
- ✅ Buscar notificaciones
- ✅ Filtrar por "Todas" o "Pendientes"
- ✅ Ver detalles completos de una notificación
- ✅ Marcar todas como leídas

---

## 🐛 Solución de Problemas

### Problema: Las notificaciones no aparecen en tiempo real

**Posibles causas:**

1. **Redis no está corriendo**
   ```bash
   redis-server
   ```

2. **El WebSocket no está conectado**
   - Revisa la consola del navegador (F12)
   - Busca mensajes de error en la consola
   - Verifica que la URL del WebSocket sea correcta

3. **El usuario no coincide**
   - El room_name del WebSocket debe coincidir con el user_id
   - Verifica en el código que el user_id sea correcto

**Verificar conexión WebSocket en el navegador:**

1. Abre DevTools (F12)
2. Ve a la pestaña "Network"
3. Filtra por "WS" (WebSocket)
4. Deberías ver una conexión activa a `ws://localhost:8000/ws/notification/<user_id>/`

### Problema: Error 500 al crear notificación

**Posibles causas:**

1. **Tipo o módulo inválido**
   - Verifica que uses los valores exactos (ej: `INFORMACION`, no `INFO`)
   - Consulta las tablas de tipos y módulos válidos arriba

2. **user_id no existe**
   - Verifica que el usuario exista en la base de datos
   - `python manage.py shell` → `UserModel.objects.get(id=1)`

### Problema: Las notificaciones se crean pero no se envían por WebSocket

**Posibles causas:**

1. **Channel layer no configurado correctamente**
   - Verifica `settings.py` → `CHANNEL_LAYERS`
   - Debe tener configurado Redis correctamente

2. **Redis no está accesible**
   ```bash
   redis-cli ping
   # Debe responder: PONG
   ```

3. **Error en la serialización**
   - Revisa los logs del servidor Django
   - Busca errores relacionados con `NotificationSerializer`

### Problema: El sonido de notificación no se reproduce

**Posibles causas:**

1. **Archivo de sonido no encontrado**
   - Verifica que el archivo existe en `public/sounds/`
   - Ruta: `tracker-frontend/public/sounds/notification.mp3`

2. **Navegador bloqueó autoplay**
   - Los navegadores bloquean sonidos automáticos por defecto
   - El usuario debe interactuar con la página primero

### Ver Logs de WebSocket

En el backend:

```bash
# Agregar prints en el consumer
# Archivo: apps/user/socket/consumers.py

async def send_notification(self, event):
    print(f"[WebSocket] Sending notification: {event['data']}")
    await self.send(text_data=json.dumps({
        'type': 'new_notification',
        'data': event['data']
    }))
```

---

## 📚 Referencias

- **Modelo**: `apps/user/models/notificacion.py`
- **Serializer**: `apps/user/serializers/notificacion.py`
- **ViewSet**: `apps/user/views/notificacion.py`
- **Consumer**: `apps/user/socket/consumers.py`
- **Frontend - Drawer**: `src/modules/ui/components/NotificationsDrawer.tsx`
- **Frontend - Page**: `src/modules/home/pages/NotificationPage.tsx`
- **Frontend - Manager**: `src/modules/ui/components/NotificationManager.tsx`

---

## 💡 Tips y Mejores Prácticas

1. **Usa el management command para pruebas rápidas**
   - Es el método más rápido y fácil
   - Incluye plantillas variadas y realistas

2. **Personaliza el script Python para casos específicos**
   - Útil para pruebas de integración
   - Fácil de modificar y adaptar

3. **Usa el endpoint REST para pruebas de API**
   - Ideal para Postman/Insomnia
   - Perfecto para pruebas automatizadas

4. **Monitorea la consola del navegador**
   - Los errores de WebSocket aparecen aquí
   - Útil para debugging en tiempo real

5. **Usa Redis Commander para ver los datos**
   ```bash
   npm install -g redis-commander
   redis-commander
   # Abre http://localhost:8081
   ```

---

## ✨ Funcionalidades Implementadas

- ✅ Notificaciones en tiempo real vía WebSocket
- ✅ Drawer de notificaciones con contador
- ✅ Página completa de notificaciones
- ✅ Búsqueda y filtrado de notificaciones
- ✅ Marcar como leídas (individual y masivo)
- ✅ Toast notifications con sonido
- ✅ Diseño responsive mobile-first
- ✅ Indicadores visuales para no leídas
- ✅ Soporte para HTML personalizado
- ✅ Datos JSON adicionales
- ✅ Navegación a URLs específicas
- ✅ Infinite scroll en la lista

---

¿Necesitas ayuda? Revisa los logs del servidor y la consola del navegador para más información.
