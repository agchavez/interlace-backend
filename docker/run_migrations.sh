#!/bin/bash

# Script para aplicar migraciones manualmente en el contenedor de producción
# Uso: cd docker && ./run_migrations.sh

echo "🚀 Aplicando migraciones en el contenedor de producción..."

# Aplicar migraciones en el contenedor web
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

echo "✅ Migraciones aplicadas exitosamente!"

# Opcional: Mostrar las migraciones pendientes
echo ""
echo "📋 Verificando estado de migraciones..."
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations


