#!/usr/bin/env python
"""
Script para crear notificaciones de prueba en tiempo real.

Este script permite crear notificaciones de prueba directamente usando la API REST.
Asegúrate de que el servidor Django esté corriendo.

Uso:
    python scripts/create_notifications.py
"""

import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8000/api"
USER_ID = 1  # ID del usuario que recibirá las notificaciones

# Token de autenticación (opcional, según tu configuración)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3ODMzMDUxLCJpYXQiOjE3Njc3OTI4MzgsImp0aSI6Ijg3ZDE0NzIxOWFmMzQ1YjFiY2NmMzdmMDFjZTM3ZWFkIiwidXNlcl9pZCI6MX0.d_NmAyZE05f-Famrt-855HZBHz_nCwud8CKKhkUvQ-s"

HEADERS = {
    "Content-Type": "application/json",
}

# Si tienes token, agrégalo a los headers
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def create_notification(notification_data):
    """Crea una notificación usando la API REST"""
    url = f"{API_BASE_URL}/notification/test/"

    try:
        response = requests.post(url, json=notification_data, headers=HEADERS)

        if response.status_code == 201:
            data = response.json()
            print(f"✓ Notificación creada exitosamente")
            print(f"  ID: {data.get('id')}")
            print(f"  Título: {data.get('title')}")
            print(f"  Usuario: {data.get('user')}")
            print(f"  WebSocket enviado: {data.get('websocket_sent', 'N/A')}")
            print(f"  URL: {API_BASE_URL}/notification/{data.get('id')}/")
            return True
        else:
            print(f"✗ Error al crear notificación: {response.status_code}")
            print(f"  Respuesta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error de conexión: {str(e)}")
        print(f"  Asegúrate de que el servidor Django esté corriendo en {API_BASE_URL}")
        return False


def main():
    print("=" * 70)
    print("🔔 GENERADOR DE NOTIFICACIONES DE PRUEBA")
    print("=" * 70)
    print(f"API: {API_BASE_URL}")
    print(f"Usuario: {USER_ID}")
    print("=" * 70)
    print()

    # Notificaciones de ejemplo
    notifications = [
        {
            "user_id": USER_ID,
            "type": "INFORMACION",
            "module": "TRACKER",
            "title": "Bienvenido al sistema de notificaciones",
            "subtitle": "Sistema configurado correctamente",
            "description": "El sistema de notificaciones en tiempo real está funcionando correctamente. Recibirás actualizaciones instantáneas sobre eventos importantes.",
            "url": "/dashboard",
            "json_data": {
                "test": True,
                "version": "1.0",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "user_id": USER_ID,
            "type": "ALERTA",
            "module": "TRACKER",
            "title": "Alerta: Acción requerida",
            "subtitle": "Documentos pendientes de revisión",
            "description": "Tienes 3 documentos pendientes de revisión que requieren tu atención inmediata. Por favor, revísalos antes del fin del día.",
            "url": "/documents/pending",
            "identifier": 789,
            "json_data": {
                "pending_count": 3,
                "priority": "high",
                "due_date": "2026-01-08"
            },
            "html": "<div style='padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107;'><strong>Documentos pendientes:</strong><ul><li>Documento 001 - Importación</li><li>Documento 002 - Exportación</li><li>Documento 003 - Inventario</li></ul></div>"
        },
        {
            "user_id": USER_ID,
            "type": "CONFIRMACION",
            "module": "TRACKER",
            "title": "Operación completada",
            "subtitle": "Pedido #12345 procesado exitosamente",
            "description": "Tu pedido ha sido procesado y confirmado. El tiempo estimado de entrega es de 2-3 días hábiles.",
            "url": "/orders/12345",
            "identifier": 12345,
            "json_data": {
                "order_id": 12345,
                "status": "confirmed",
                "items": 5,
                "total": 1250.50
            }
        },
        {
            "user_id": USER_ID,
            "type": "RECORDATORIO",
            "module": "USUARIO",
            "title": "Recordatorio: Reunión en 1 hora",
            "subtitle": "Reunión de revisión mensual",
            "description": "Tienes una reunión programada en 1 hora. Tema: Revisión de métricas de desempeño del mes. Ubicación: Sala de conferencias B.",
            "url": "/calendar",
            "json_data": {
                "meeting_time": "15:00",
                "attendees": ["Juan Pérez", "María González", "Carlos Ruiz"],
                "duration": "60 minutos"
            }
        },
        {
            "user_id": USER_ID,
            "type": "ADVERTENCIA",
            "module": "TRACKER",
            "title": "Advertencia: Stock bajo",
            "subtitle": "Productos con inventario crítico",
            "description": "Se han detectado 8 productos con niveles de stock por debajo del mínimo establecido. Se recomienda realizar un pedido de reabastecimiento.",
            "url": "/inventory/low-stock",
            "json_data": {
                "critical_products": 8,
                "minimum_threshold": 10,
                "average_stock": 5
            }
        },
        {
            "user_id": USER_ID,
            "type": "UBICACION",
            "module": "T2",
            "title": "Rastreo actualizado",
            "subtitle": "Paquete #T2-98765 en tránsito",
            "description": "Tu paquete ha llegado al centro de distribución regional. Siguiente parada: Centro de distribución local. ETA: Mañana 10:00 AM.",
            "url": "/tracking/T2-98765",
            "identifier": 98765,
            "json_data": {
                "tracking_number": "T2-98765",
                "current_location": "Centro de Distribución Regional",
                "next_location": "Centro de Distribución Local",
                "eta": "2026-01-08 10:00"
            },
            "html": "<div style='font-family: monospace;'><strong>📍 Ruta del paquete:</strong><br/>✓ Origen - Lima (07/01 08:00)<br/>✓ Hub Principal (07/01 14:00)<br/><strong>→ CD Regional (07/01 18:00) ACTUAL</strong><br/>⏱ CD Local (08/01 08:00)<br/>⏱ Destino (08/01 10:00)</div>"
        },
    ]

    print(f"Creando {len(notifications)} notificaciones de prueba...\n")

    success_count = 0
    for i, notification in enumerate(notifications, 1):
        print(f"[{i}/{len(notifications)}] Creando notificación: {notification['title']}")
        if create_notification(notification):
            success_count += 1
        print()

    print("=" * 70)
    print(f"✓ Completado: {success_count}/{len(notifications)} notificaciones creadas")
    print("=" * 70)
    print()
    print("💡 Consejos:")
    print("  - Abre el navegador en http://localhost:3000")
    print("  - Inicia sesión con el usuario ID 1")
    print("  - Observa el ícono de notificaciones en la barra superior")
    print("  - Haz clic para ver el drawer de notificaciones")
    print("  - Ve a /notifications para ver la página completa")
    print()


if __name__ == "__main__":
    main()
