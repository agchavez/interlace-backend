# Tracker Backend - Sistema de Logística

Backend API REST desarrollado en Django para un sistema de seguimiento logístico. La aplicación gestiona pedidos, inventario, seguimiento, datos de mantenimiento y manejo de documentos con Celery para tareas en segundo plano y soporte WebSocket para notificaciones en tiempo real.

## 🚀 Características Principales

- **API REST** completa con Django REST Framework
- **Autenticación JWT** segura
- **Seguimiento en tiempo real** con WebSockets
- **Tareas programadas** con Celery
- **Almacenamiento en la nube** con Azure Blob Storage
- **Notificaciones** en tiempo real
- **Gestión de inventario** y pedidos
- **Reportes y dashboard**

## 🛠️ Tecnologías

- **Django 4.2** + Django REST Framework
- **PostgreSQL** como base de datos principal
- **Redis** para broker de Celery y canal de WebSockets
- **Celery** con django-celery-beat para tareas programadas
- **Django Channels** para soporte WebSocket
- **Azure Blob Storage** para archivos multimedia
- **JWT** para autenticación

## 📦 Instalación

### Prerrequisitos

- Python 3.8+
- PostgreSQL
- Redis
- pip

### Instalación Local

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd tracker-backend
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   Crear un archivo `.env` en la raíz del proyecto:
   ```env
   DEBUG=True
   DB_NAME=tracker_db
   DB_USER=postgres
   DB_PASSWORD=tu_password
   DB_HOST=localhost
   DB_PORT=5432
   
   EMAIL_USE_TLS=True
   EMAIL_HOST=smtp.gmail.com
   EMAIL_HOST_USER=tu_email@gmail.com
   EMAIL_HOST_PASSWORD=tu_password
   EMAIL_PORT=587
   
   CELERY_BROKER_REDIS_URL=redis://localhost:6379
   ```

5. **Ejecutar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

### Instalación con Docker

1. **Ejecutar con Docker Compose**
   ```bash
   docker-compose up --build
   ```

   Esto iniciará todos los servicios necesarios:
   - Base de datos PostgreSQL
   - Redis
   - Aplicación Django
   - Celery Worker
   - Celery Beat

## 🎯 Uso

### Comandos de Desarrollo

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Celery Worker
celery -A config worker -l info

# Celery Beat (tareas programadas)
celery -A config beat

# Cargar datos iniciales
python manage.py load_data

# Crear usuarios programáticamente
python manage.py create_user

# Actualizar datos de tracker
python manage.py update_tracker
```

### API Endpoints

La API está disponible en `/api/` con los siguientes módulos:

- **Autenticación**: `/api/auth/`
- **Usuarios**: `/api/users/`
- **Mantenimiento**: `/api/maintenance/`
- **Tracker**: `/api/tracker/`
- **Pedidos**: `/api/orders/`
- **Inventario**: `/api/inventory/`
- **Reportes**: `/api/reports/`
- **Documentos**: `/api/documents/`

### Autenticación

La API utiliza autenticación JWT. Para obtener tokens:

```bash
POST /api/auth/login/
{
    "username": "tu_usuario",
    "password": "tu_password"
}
```

Incluir el token en las peticiones:
```
Authorization: Bearer <tu_token>
```

## 🏗️ Arquitectura

### Estructura del Proyecto

```
apps/
├── authentication/     # Sistema de autenticación JWT
├── user/              # Gestión de usuarios y notificaciones
├── maintenance/       # Datos maestros (conductores, productos, etc.)
├── tracker/           # Funcionalidad principal de seguimiento
├── order/             # Gestión de pedidos
├── inventory/         # Gestión de inventario
├── report/            # Reportes y dashboard
├── document/          # Manejo de documentos e imágenes
└── imported/          # Funcionalidad de importación/exportación

config/                # Configuración de Django
utils/                 # Utilidades compartidas
middleware/            # Middleware personalizado
```

### Modelos Principales

- **UserModel**: Usuario personalizado con relaciones a centros de distribución
- **TrackerModel**: Seguimiento principal con soporte T2
- **OrderModel**: Gestión de pedidos con historial
- **InventoryModel**: Control de inventario
- **ProductModel**: Catálogo de productos

### Tareas en Segundo Plano

El sistema utiliza Celery para tareas asíncronas:

- Procesamiento de documentos
- Envío de notificaciones
- Actualización de datos de seguimiento
- Generación de reportes

## 🔧 Configuración

### Variables de Entorno

Las principales variables de entorno son:

```env
# Base de datos
DB_NAME=nombre_bd
DB_USER=usuario_bd
DB_PASSWORD=password_bd
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp_host
EMAIL_HOST_USER=email_usuario
EMAIL_HOST_PASSWORD=email_password
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Redis/Celery
CELERY_BROKER_REDIS_URL=redis://localhost:6379

# Azure Storage (opcional)
AZURE_ACCOUNT_NAME=tu_cuenta
AZURE_ACCOUNT_KEY=tu_clave
AZURE_CONTAINER=contenedor
```

### Configuración de Zona Horaria

El sistema está configurado para:
- **Zona horaria**: America/Tegucigalpa
- **Idioma**: Español (Honduras) - es-HN
- **USE_TZ**: True para manejo de zonas horarias

## 🧪 Pruebas

```bash
# Ejecutar todas las pruebas
python manage.py test

# Ejecutar pruebas de una app específica
python manage.py test apps.tracker

# Ejecutar con cobertura
coverage run --source='.' manage.py test
coverage report
```

## 📝 Comandos de Gestión

### Usuarios
```bash
# Crear usuario
python manage.py create_user

# Actualizar usuario
python manage.py update_user
```

### Datos
```bash
# Cargar datos iniciales
python manage.py load_data

# Actualizar tracker
python manage.py update_tracker

# Crear tareas programadas
python manage.py create_task
```

## 🚀 Despliegue

### Consideraciones de Producción

1. **Variables de entorno**: Configurar todas las variables necesarias
2. **Base de datos**: Usar PostgreSQL en producción
3. **Redis**: Configurar Redis para Celery y WebSockets
4. **Archivos estáticos**: Configurar servicio de archivos
5. **HTTPS**: Habilitar SSL/TLS
6. **Monitoreo**: Configurar logs y monitoreo de Celery

### Docker en Producción

```bash
# Construir imagen
docker build -t tracker-backend .

# Ejecutar con variables de entorno
docker run -d --env-file .env tracker-backend
```

## 📄 Licencia

Este proyecto es privado y pertenece a ACSolutions.

## 📞 Soporte

Para soporte técnico, contactar al equipo de desarrollo.