# 🚀 Script de despliegue rápido para producción
# Uso: cd docker; .\deploy.ps1

param(
    [switch]$NoBuild,
    [switch]$Logs
)

Write-Host "🚀 Desplegando aplicación en producción..." -ForegroundColor Green
Write-Host ""

$composeFile = "docker-compose.prod.yml"

if ($NoBuild) {
    Write-Host "⏩ Omitiendo construcción de imágenes..." -ForegroundColor Yellow
    docker-compose -f $composeFile up -d
} else {
    Write-Host "🔨 Construyendo imágenes..." -ForegroundColor Cyan
    docker-compose -f $composeFile up -d --build
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Despliegue exitoso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Estado de los contenedores:" -ForegroundColor Cyan
    docker-compose -f $composeFile ps

    if ($Logs) {
        Write-Host ""
        Write-Host "📋 Mostrando logs (Ctrl+C para salir)..." -ForegroundColor Cyan
        docker-compose -f $composeFile logs -f
    } else {
        Write-Host ""
        Write-Host "💡 Comandos útiles:" -ForegroundColor Yellow
        Write-Host "  Ver logs:        docker-compose -f $composeFile logs -f" -ForegroundColor White
        Write-Host "  Ver estado:      docker-compose -f $composeFile ps" -ForegroundColor White
        Write-Host "  Detener todo:    docker-compose -f $composeFile down" -ForegroundColor White
        Write-Host "  Ver migraciones: docker-compose -f $composeFile exec web python manage.py showmigrations" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "❌ Error en el despliegue" -ForegroundColor Red
    Write-Host "Ver logs con: docker-compose -f $composeFile logs" -ForegroundColor Yellow
    exit 1
}

