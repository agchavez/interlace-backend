# 🚀 Configuración de Realtime con Daphne y Migraciones Automáticas

## 🎯 Arquitectura Actual

### **Servidor ASGI con Daphne**
Tu aplicación usa **Daphne** en lugar de Gunicorn porque necesitas:
- ✅ **WebSockets** para comunicación en tiempo real
- ✅ **Django Channels** para notificaciones push
- ✅ **ASGI** (Asynchronous Server Gateway Interface)

### **Diferencia con Gunicorn:**
```
❌ Gunicorn = Solo HTTP (WSGI) - Sin WebSockets
✅ Daphne = HTTP + WebSockets (ASGI) - Realtime
```

---

## 🔄 Flujo de Inicio del Contenedor

### 1. **Entrypoint Script (`/entrypoint.sh`)** 
Se ejecuta PRIMERO antes de cualquier cosa:

```bash
🔍 Esperando a que la base de datos esté disponible...
✅ Base de datos disponible!

📦 Aplicando migraciones de base de datos...
   ↳ python manage.py migrate --noinput

📊 Recolectando archivos estáticos...
   ↳ python manage.py collectstatic --noinput --clear

🚀 Iniciando aplicación...
   ↳ daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 2. **Resultado:**
- ✅ Las migraciones se aplican AUTOMÁTICAMENTE antes de iniciar Daphne
- ✅ No necesitas aplicarlas manualmente
- ✅ Siempre tienes la BD actualizada

---

## 📦 Servicios en Docker Compose

```yaml
services:
  web:
    # Usa Daphne para soportar WebSockets
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    entrypoint: ["/entrypoint.sh"]  # ← Aplica migraciones aquí
    
  redis:
    # Usado por Channels (WebSockets) y Celery
    image: redis:latest
    
  celery-worker:
    # Workers para tareas asíncronas
    command: celery -A config worker -l info
    
  celery-beat:
    # Scheduler para tareas periódicas
    command: celery -A config beat -l info
```

---

## ⚙️ Configuración de Redis

### **Variables de Entorno Requeridas:**

```env
# Redis para Channels (WebSockets)
REDIS_HOST=redis  # Nombre del servicio en docker-compose
REDIS_PORT=6379

# Redis para Celery
CELERY_BROKER_REDIS_URL=redis://redis:6379/0
```

### **En settings.py:**

```python
# Para Django Channels (WebSockets)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.getenv('REDIS_HOST', 'localhost'), 
                      int(os.getenv('REDIS_PORT', '6379')))],
        },
    },
}

# Para Celery
CELERY_BROKER_URL = config('CELERY_BROKER_REDIS_URL', 
                          default='redis://localhost:6379')
```

---

## 🔍 Verificar que Todo Funciona

### 1. **Verificar que las migraciones se aplicaron:**

```powershell
cd docker
docker-compose -f docker-compose.prod.yml logs web
```

Deberías ver:
```
web_1  | 🔍 Esperando a que la base de datos esté disponible...
web_1  | ✅ Base de datos disponible!
web_1  | 📦 Aplicando migraciones de base de datos...
web_1  | Running migrations:
web_1  |   Applying contenttypes.0001_initial... OK
web_1  |   Applying auth.0001_initial... OK
web_1  |   ...
web_1  | 🚀 Iniciando aplicación...
web_1  | Daphne running at 0.0.0.0:8000
```

### 2. **Verificar estado de migraciones:**

```powershell
cd docker
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

### 3. **Probar WebSockets:**

```javascript
// En el frontend
const ws = new WebSocket('ws://tu-dominio.com/ws/notifications/');

ws.onopen = () => {
    console.log('✅ WebSocket conectado');
};

ws.onmessage = (event) => {
    console.log('📨 Mensaje recibido:', event.data);
};
```

---

## 🚀 Desplegar

### **Opción 1: Script Automatizado**
```powershell
cd docker
.\deploy.ps1 -Logs
```

### **Opción 2: Manual**
```powershell
cd docker
docker-compose -f docker-compose.prod.yml up -d --build
```

### **Ver logs en tiempo real:**
```powershell
cd docker
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## 📝 Notas Importantes

### **¿Por qué Daphne en lugar de Gunicorn?**

| Característica | Gunicorn | Daphne |
|----------------|----------|--------|
| Protocolo | WSGI | ASGI |
| HTTP | ✅ | ✅ |
| WebSockets | ❌ | ✅ |
| Realtime | ❌ | ✅ |
| Django Channels | ❌ | ✅ |

### **¿Cuándo se aplican las migraciones?**

Las migraciones se aplican **AUTOMÁTICAMENTE** cuando:
1. ✅ Inicias el contenedor por primera vez
2. ✅ Reinicias el contenedor
3. ✅ Haces un nuevo deploy
4. ✅ Ejecutas `docker-compose up`

**NO necesitas aplicarlas manualmente** a menos que:
- Quieras forzar la aplicación fuera del flujo normal
- Estés debugeando problemas específicos

---

## 🔧 Comandos Útiles

### **Ver estado de todos los servicios:**
```powershell
cd docker
docker-compose -f docker-compose.prod.yml ps
```

### **Reiniciar solo el servicio web:**
```powershell
cd docker
docker-compose -f docker-compose.prod.yml restart web
```

### **Ver logs de Redis:**
```powershell
cd docker
docker-compose -f docker-compose.prod.yml logs -f redis
```

### **Ver logs de Celery:**
```powershell
cd docker
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

### **Ejecutar comandos Django:**
```powershell
cd docker

# Crear superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Shell interactivo
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Ver rutas
docker-compose -f docker-compose.prod.yml exec web python manage.py show_urls
```

---

## ✅ Checklist de Configuración

- [x] Daphne configurado en docker-compose
- [x] Entrypoint aplicando migraciones automáticamente
- [x] Redis configurado para Channels y Celery
- [x] Variables de entorno configuradas
- [x] ASGI configurado en settings.py
- [x] Channels instalado y configurado

---

## 🎉 ¡Todo Listo!

Tu aplicación ahora:
- ✅ Usa Daphne para WebSockets y realtime
- ✅ Aplica migraciones automáticamente al iniciar
- ✅ Tiene Redis configurado para Channels y Celery
- ✅ Está lista para producción

### Para desplegar:
```powershell
cd docker
.\deploy.ps1
```

**¡Disfruta de tu aplicación en tiempo real!** 🚀

