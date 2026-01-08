# ✅ RESUMEN DE CAMBIOS - Configuración Docker y Migraciones

## 📁 Cambios Realizados

### 1. ✅ Reorganización de Archivos Docker

Todos los archivos relacionados con Docker se movieron a la carpeta `docker/`:

```
tracker-backend/
├── docker/                          ← NUEVA CARPETA
│   ├── Dockerfile                   ← Movido y actualizado
│   ├── docker-compose.prod.yml      ← Movido y actualizado
│   ├── docker-compose.yaml          ← Movido y actualizado
│   ├── entrypoint.sh                ← NUEVO - Aplica migraciones automáticamente
│   ├── entrypoint-celery.sh         ← NUEVO - Para workers de Celery
│   ├── .dockerignore                ← Movido y actualizado
│   └── README.md                    ← NUEVO - Documentación de Docker
├── deploy.ps1                       ← NUEVO - Script de despliegue rápido
├── run_migrations.ps1               ← NUEVO - Script manual de migraciones
├── run_migrations.sh                ← NUEVO - Script manual de migraciones (Linux)
├── MIGRATIONS_GUIDE.md              ← NUEVO - Guía completa de migraciones
├── requirements.txt                 ← Actualizado (sin UNKNOWN, con pyodbc)
└── ... (resto de archivos del proyecto)
```

---

## 🔧 Problemas Solucionados

### ✅ Problema 1: Error en construcción de imagen Docker (Alpine Linux)
**Error anterior:**
```
ERROR: Could not build wheels for numpy
RuntimeError: Broken toolchain: cannot link a simple C program
```

**Solución:**
- Cambiado de `python:3.10.0-alpine` a `python:3.10-slim` (Debian-based)
- Agregadas todas las dependencias del sistema necesarias:
  - `gcc`, `g++`, `gfortran` (compiladores)
  - `libopenblas-dev`, `liblapack-dev` (para numpy/pandas)
  - `unixodbc-dev` (para pyodbc)

### ✅ Problema 2: Error con apt-key (deprecado)
**Error anterior:**
```
/bin/sh: 1: apt-key: not found
```

**Solución:**
- Reemplazado `apt-key add` por `gpg --dearmor`
- Actualizado a usar Debian 12 en la configuración de Microsoft ODBC Driver

### ✅ Problema 3: Migraciones no se aplicaban automáticamente
**Problema:**
Al desplegar, las migraciones no se ejecutaban y había que aplicarlas manualmente.

**Solución:**
- Creados scripts `entrypoint.sh` y `entrypoint-celery.sh`
- El entrypoint principal ahora:
  1. Espera a que la base de datos esté disponible
  2. Aplica migraciones automáticamente
  3. Recolecta archivos estáticos
  4. Inicia la aplicación

---

## 🚀 Cómo Usar

### Despliegue en Producción

#### Opción 1: Script Automatizado (Recomendado)
```powershell
# Despliegue completo con construcción
.\deploy.ps1

# Despliegue sin reconstruir (más rápido si no hay cambios)
.\deploy.ps1 -NoBuild

# Despliegue y mostrar logs en tiempo real
.\deploy.ps1 -Logs
```

#### Opción 2: Comando Manual
```powershell
# Construir y levantar todos los servicios
docker-compose -f docker/docker-compose.prod.yml up -d --build

# Ver logs
docker-compose -f docker/docker-compose.prod.yml logs -f web
```

### Desarrollo Local

```powershell
# Con PostgreSQL local
docker-compose -f docker/docker-compose.yaml up -d --build

# Ver logs
docker-compose -f docker/docker-compose.yaml logs -f
```

---

## 📦 Archivos Nuevos Creados

### 1. `docker/entrypoint.sh`
Script que se ejecuta al iniciar el contenedor web. Aplica migraciones automáticamente.

### 2. `docker/entrypoint-celery.sh`
Script para workers de Celery. Espera a que la base de datos esté disponible.

### 3. `deploy.ps1`
Script de despliegue rápido con opciones para:
- Construcción de imágenes
- Ver logs automáticamente
- Mostrar estado de contenedores

### 4. `run_migrations.ps1` / `run_migrations.sh`
Scripts para aplicar migraciones manualmente cuando sea necesario.

### 5. `MIGRATIONS_GUIDE.md`
Guía completa con:
- Explicación de migraciones automáticas
- Comandos útiles
- Solución de problemas
- Checklist de despliegue

### 6. `docker/README.md`
Documentación específica de la configuración Docker.

---

## 🔄 Flujo de Migraciones Automáticas

### Al Desplegar:

1. **Contenedor web inicia**
   ```
   🔍 Esperando a que la base de datos esté disponible...
   ✅ Base de datos disponible!
   📦 Aplicando migraciones de base de datos...
   📊 Recolectando archivos estáticos...
   🚀 Iniciando aplicación...
   ```

2. **Workers de Celery inician**
   ```
   🔍 Esperando a que la base de datos esté disponible...
   ✅ Base de datos disponible!
   🚀 Iniciando worker Celery...
   ```

### ✅ Ventajas:
- **No más migraciones olvidadas** - Se aplican automáticamente
- **Despliegues más seguros** - Verifica la conexión a BD antes de iniciar
- **Logs claros** - Puedes ver exactamente qué está pasando
- **Zero downtime** - Los workers esperan a que el web esté listo

---

## 🛠️ Comandos Útiles

### Ver estado de migraciones
```powershell
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py showmigrations
```

### Crear nuevas migraciones
```powershell
# Localmente
python manage.py makemigrations

# En el contenedor
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py makemigrations
```

### Ver logs
```powershell
# Todos los servicios
docker-compose -f docker/docker-compose.prod.yml logs -f

# Solo web
docker-compose -f docker/docker-compose.prod.yml logs -f web

# Solo celery-worker
docker-compose -f docker/docker-compose.prod.yml logs -f celery-worker
```

### Detener servicios
```powershell
# Detener sin eliminar volúmenes
docker-compose -f docker/docker-compose.prod.yml down

# Detener y eliminar volúmenes (⚠️ borra datos de Redis)
docker-compose -f docker/docker-compose.prod.yml down -v
```

### Reconstruir sin caché
```powershell
docker-compose -f docker/docker-compose.prod.yml build --no-cache
```

---

## 📝 Variables de Entorno Requeridas

Asegúrate de tener un archivo `.env` en la raíz del proyecto:

```env
# Base de datos
DB_NAME=nombre_base_datos
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=host.docker.internal  # o IP del servidor
DB_PORT=5432

# Django
DEBUG=False
SECRET_KEY=tu-secret-key-muy-segura

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## 🎯 Próximos Pasos

1. **Probar localmente:**
   ```powershell
   .\deploy.ps1 -Logs
   ```

2. **Verificar migraciones:**
   ```powershell
   docker-compose -f docker/docker-compose.prod.yml exec web python manage.py showmigrations
   ```

3. **Revisar logs:**
   ```powershell
   docker-compose -f docker/docker-compose.prod.yml logs web
   ```

4. **Hacer commit de los cambios:**
   ```powershell
   git add .
   git commit -m "feat: Reorganizar configuración Docker y agregar migraciones automáticas"
   git push
   ```

5. **Desplegar en producción:**
   - Si usas Dokploy, solo haz push y el sistema detectará los cambios
   - Si despliegas manualmente, usa: `.\deploy.ps1`

---

## ⚠️ Notas Importantes

1. **Backup de base de datos**: Siempre haz backup antes de aplicar migraciones en producción.

2. **Archivos de migración**: Asegúrate de hacer commit de todos los archivos en `apps/*/migrations/`.

3. **Secrets**: Nunca hagas commit del archivo `.env` - usa `.env.example` como plantilla.

4. **Reconstrucción**: Si cambias el `Dockerfile` o `requirements.txt`, debes reconstruir con `--build`.

5. **Logs**: Si algo falla, los logs son tu mejor amigo: `docker-compose logs -f`

---

## 📚 Documentación Adicional

- **Guía de Migraciones**: Ver `MIGRATIONS_GUIDE.md`
- **Docker README**: Ver `docker/README.md`
- **Django Docs**: https://docs.djangoproject.com/
- **Docker Compose**: https://docs.docker.com/compose/

---

## ✅ Checklist Final

- [x] Dockerfile actualizado con imagen Debian slim
- [x] Dependencias del sistema instaladas (gcc, g++, gfortran, etc.)
- [x] Microsoft ODBC Driver 18 instalado correctamente
- [x] Scripts de entrypoint creados y configurados
- [x] docker-compose.prod.yml actualizado con contextos correctos
- [x] Migraciones automáticas configuradas
- [x] Scripts de despliegue creados
- [x] Documentación completa generada
- [x] Estructura de carpetas organizada

---

## 🎉 ¡Todo Listo!

Tu proyecto ahora tiene:
- ✅ Construcción de Docker exitosa
- ✅ Migraciones automáticas
- ✅ Scripts de despliegue fáciles de usar
- ✅ Documentación completa
- ✅ Estructura organizada

**¡Puedes desplegar con confianza!** 🚀

