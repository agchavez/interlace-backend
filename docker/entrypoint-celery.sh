#!/bin/bash

# Script de entrada para Celery workers
# Solo espera a que la base de datos esté disponible

set -e

echo "🔍 Esperando a que la base de datos esté disponible..."

# Esperar a que la base de datos esté lista
python << END
import sys
import time
import psycopg2
from decouple import config

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD'),
            host=config('DB_HOST'),
            port=config('DB_PORT', default='5432')
        )
        conn.close()
        print("✅ Base de datos disponible!")
        sys.exit(0)
    except psycopg2.OperationalError:
        retry_count += 1
        print(f"⏳ Intento {retry_count}/{max_retries} - Esperando base de datos...")
        time.sleep(2)

print("❌ No se pudo conectar a la base de datos después de varios intentos")
sys.exit(1)
END

echo "🚀 Iniciando worker Celery..."
exec "$@"

