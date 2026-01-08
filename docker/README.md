# 📁 Carpeta Docker

Esta carpeta contiene todos los archivos relacionados con Docker para el proyecto.

## 📄 Archivos

### `Dockerfile`
Archivo de construcción de la imagen Docker. Define:
- Imagen base: `python:3.10-slim`
- Dependencias del sistema (gcc, g++, gfortran, ODBC drivers, etc.)
- Instalación de Microsoft ODBC Driver 18 para SQL Server
- Configuración de scripts de entrypoint
- Instalación de dependencias de Python

### `docker-compose.prod.yml`
Configuración de Docker Compose para **producción**. Define:
- **web**: Servicio principal Django con Gunicorn
- **redis**: Servicio Redis para caché y cola de mensajes
- **celery-worker**: Workers de Celery para tareas asíncronas
- **celery-beat**: Scheduler de Celery para tareas periódicas

### `docker-compose.yaml`
Configuración de Docker Compose para **desarrollo**. Incluye:
- **db**: PostgreSQL 15 para base de datos local
- **web**: Servicio Django con auto-reload
- **redis**: Redis para desarrollo
- **celery-worker**: Workers de Celery
- **celery-beat**: Scheduler de Celery

### `entrypoint.sh`
Script de entrada para el contenedor **web**. Ejecuta:
1. ✅ Verifica conexión a la base de datos
2. ✅ Aplica migraciones automáticamente
3. ✅ Recolecta archivos estáticos
4. ✅ Inicia la aplicación

### `entrypoint-celery.sh`
Script de entrada para contenedores **celery-worker** y **celery-beat**. Ejecuta:
1. ✅ Verifica conexión a la base de datos
2. ✅ Inicia el worker/beat de Celery

### `.dockerignore`
Lista de archivos y carpetas que se excluyen al construir la imagen Docker.

---

## 🚀 Uso

### Producción

```powershell
# Construir y levantar servicios
docker-compose -f docker/docker-compose.prod.yml up -d --build

# Ver logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Detener servicios
docker-compose -f docker/docker-compose.prod.yml down

# Detener y eliminar volúmenes
docker-compose -f docker/docker-compose.prod.yml down -v
```

### Desarrollo

```powershell
# Construir y levantar servicios (incluye PostgreSQL)
docker-compose -f docker/docker-compose.yaml up -d --build

# Ver logs
docker-compose -f docker/docker-compose.yaml logs -f

# Detener servicios
docker-compose -f docker/docker-compose.yaml down
```

---

## ⚙️ Configuración

### Variables de Entorno

Asegúrate de tener un archivo `.env` en la raíz del proyecto con:

```env
# Base de datos
DB_NAME=nombre_base_datos
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=host.docker.internal  # o la IP de tu servidor
DB_PORT=5432

# Django
DEBUG=False
SECRET_KEY=tu-secret-key-segura

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## 🔄 Migraciones

Las migraciones se aplican **automáticamente** al iniciar el contenedor web gracias al script `entrypoint.sh`.

Para más información sobre migraciones, consulta el archivo `MIGRATIONS_GUIDE.md` en la raíz del proyecto.

---

## 🐛 Troubleshooting

### Error: "no such file or directory: /entrypoint.sh"

Reconstruye la imagen sin caché:
```powershell
docker-compose -f docker/docker-compose.prod.yml build --no-cache
```

### Error: "permission denied: /entrypoint.sh"

El Dockerfile ya incluye `chmod +x` para los scripts. Si persiste, verifica que los scripts tengan finales de línea Unix (LF) y no Windows (CRLF).

### El contenedor web no inicia

Verifica los logs:
```powershell
docker-compose -f docker/docker-compose.prod.yml logs web
```

Verifica la conexión a la base de datos:
```powershell
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py dbshell
```

---

## 📚 Estructura del Proyecto

```
tracker-backend/
├── docker/                    # ← Estás aquí
│   ├── Dockerfile
│   ├── docker-compose.prod.yml
│   ├── docker-compose.yaml
│   ├── entrypoint.sh
│   ├── entrypoint-celery.sh
│   ├── .dockerignore
│   └── README.md
├── apps/
├── config/
├── requirements.txt
├── manage.py
├── .env
└── MIGRATIONS_GUIDE.md
```

---

## 🔗 Enlaces Útiles

- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de Docker Compose](https://docs.docker.com/compose/)
- [Guía de Migraciones](../MIGRATIONS_GUIDE.md)
- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de Celery](https://docs.celeryproject.org/)

