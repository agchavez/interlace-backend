# 🚀 Guía de Migraciones y Despliegue

## ✅ Migraciones Automáticas

### ¿Cómo funciona?

Ahora las migraciones se aplican **automáticamente** cada vez que despliegas la aplicación. Esto se logra mediante scripts de entrypoint que se ejecutan antes de iniciar los servicios.

### Flujo de inicio:

1. **Contenedor `web` inicia**
   - ✅ Espera a que la base de datos esté disponible
   - ✅ Aplica migraciones automáticamente (`python manage.py migrate`)
   - ✅ Recolecta archivos estáticos (`python manage.py collectstatic`)
   - ✅ Inicia Gunicorn

2. **Contenedores `celery-worker` y `celery-beat` inician**
   - ✅ Esperan a que la base de datos esté disponible
   - ✅ Esperan a que el servicio `web` esté listo
   - ✅ Inician los workers de Celery

---

## 📦 Archivos Creados

### 1. `entrypoint.sh`
Script principal que ejecuta el contenedor `web`. Realiza:
- Verificación de conexión a la base de datos
- Aplicación automática de migraciones
- Recolección de archivos estáticos
- Inicio de la aplicación

### 2. `entrypoint-celery.sh`
Script para workers de Celery. Solo verifica la conexión a la base de datos antes de iniciar.

### 3. `run_migrations.ps1` / `run_migrations.sh`
Scripts opcionales para aplicar migraciones manualmente cuando sea necesario.

---

## 🔧 Comandos Útiles

### Desplegar con migraciones automáticas
```powershell
# Opción 1: Usar el script de despliegue
cd docker
.\deploy.ps1

# Opción 2: Comando directo
cd docker
docker-compose -f docker-compose.prod.yml up -d --build

# Ver los logs para confirmar que las migraciones se aplicaron
docker-compose -f docker-compose.prod.yml logs web
```

### Aplicar migraciones manualmente (opcional)
```powershell
# Opción 1: Usar el script PowerShell
cd docker
.\run_migrations.ps1

# Opción 2: Ejecutar directamente
cd docker
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Ver el estado de las migraciones
```powershell
cd docker
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

### Crear nuevas migraciones
```powershell
# Desde el contenedor en ejecución
cd docker
docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations

# O desde tu máquina local (recomendado para desarrollo)
python manage.py makemigrations
```

### Revertir migraciones
```powershell
cd docker

# Revertir la última migración de una app específica
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate app_name previous

# Revertir a una migración específica
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate app_name 0001
```

### Ver logs en tiempo real
```powershell
cd docker

# Ver logs de todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Ver solo logs del servicio web
docker-compose -f docker-compose.prod.yml logs -f web

# Ver logs de Celery worker
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

---

## 🐛 Solución de Problemas

### Las migraciones no se aplican

1. **Verificar que el servicio web esté ejecutándose:**
   ```powershell
   docker-compose -f docker/docker-compose.prod.yml ps
   ```

2. **Ver los logs del servicio web:**
   ```powershell
   docker-compose -f docker/docker-compose.prod.yml logs web
   ```

3. **Verificar conexión a la base de datos:**
   ```powershell
   docker-compose -f docker/docker-compose.prod.yml exec web python manage.py dbshell
   ```

### Error "no module named psycopg2"

Asegúrate de que `psycopg2-binary==2.9.7` esté en tu `requirements.txt`.

### Error de permisos en scripts .sh

Los scripts deberían tener permisos de ejecución. Si hay problemas, reconstruye la imagen:
```powershell
docker-compose -f docker/docker-compose.prod.yml build --no-cache
```

### Las migraciones se ejecutan múltiples veces

Esto es normal y seguro. Django detecta automáticamente qué migraciones ya se aplicaron y solo aplica las nuevas.

---

## 📋 Checklist de Despliegue

Antes de desplegar a producción:

- [ ] ✅ Crear las migraciones localmente: `python manage.py makemigrations`
- [ ] ✅ Probar las migraciones localmente: `python manage.py migrate`
- [ ] ✅ Commit de los archivos de migración
- [ ] ✅ Push al repositorio
- [ ] ✅ Desplegar con docker-compose: `docker-compose -f docker/docker-compose.prod.yml up -d --build`
- [ ] ✅ Verificar logs: `docker-compose -f docker/docker-compose.prod.yml logs web`
- [ ] ✅ Verificar estado: `docker-compose -f docker/docker-compose.prod.yml exec web python manage.py showmigrations`

---

## 🔐 Variables de Entorno Requeridas

Asegúrate de que tu archivo `.env` contenga:

```env
DB_NAME=nombre_base_datos
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=host.docker.internal  # o la IP de tu servidor de BD
DB_PORT=5432
DEBUG=False
```

---

## 🚨 Importante

- **Las migraciones se aplican automáticamente** al iniciar el contenedor web
- **No es necesario aplicarlas manualmente** a menos que quieras hacerlo por alguna razón específica
- **Siempre haz backup de tu base de datos** antes de aplicar migraciones en producción
- **Los workers de Celery esperan** a que el servicio web esté listo antes de iniciar

---

## 📚 Recursos Adicionales

- [Documentación oficial de Django Migrations](https://docs.djangoproject.com/en/4.2/topics/migrations/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

