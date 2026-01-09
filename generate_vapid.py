"""
Genera claves VAPID para Web Push Notifications
"""
from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64

# Generar nuevas claves
vapid = Vapid()
vapid.generate_keys()

# Obtener la clave privada en formato PEM
private_key_pem = vapid.private_pem().decode('utf-8')

# Obtener la clave pública en formato URL-safe base64
public_key_bytes = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

print("=" * 60)
print("CLAVES VAPID GENERADAS")
print("=" * 60)
print("\nClave Privada (VAPID_PRIVATE_KEY):")
print(private_key_pem)
print("\nClave Pública (VAPID_PUBLIC_KEY):")
print(public_key_b64)
print("\n" + "=" * 60)
print("\nAgrega estas líneas a tu archivo .env:")
print("=" * 60)
# Convertir saltos de línea a \\n para el .env
private_key_oneline = private_key_pem.replace('\n', '\\n')
print(f'\nVAPID_PRIVATE_KEY={private_key_oneline}')
print(f'VAPID_PUBLIC_KEY={public_key_b64}')
print('VAPID_ADMIN_EMAIL=admin@tracker.alt')
print("\n" + "=" * 60)
