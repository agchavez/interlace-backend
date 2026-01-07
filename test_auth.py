"""
Script para probar la creación y autenticación de usuarios
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password

User = get_user_model()

def test_user_creation():
    """Prueba de creación y autenticación de usuario"""

    # Datos de prueba
    test_email = "test_user_temp@example.com"
    test_password = "TestPassword123"
    test_username = "testuser_temp"

    # Limpiar usuario de prueba si existe
    User.objects.filter(email=test_email).delete()

    print("\n" + "="*60)
    print("PRUEBA 1: Crear usuario con create_user()")
    print("="*60)

    # Crear usuario usando create_user
    user = User.objects.create_user(
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )

    print(f"[OK] Usuario creado: {user.email}")
    print(f"  Password hash: {user.password[:50]}...")
    print(f"  check_password(): {check_password(test_password, user.password)}")

    # Intentar autenticar
    auth_user = authenticate(email=test_email, password=test_password)
    print(f"  authenticate(): {'[OK] EXITOSO' if auth_user else '[FALLO] FALLO'}")

    print("\n" + "="*60)
    print("PRUEBA 2: Simular lo que hace create_with_user (con save())")
    print("="*60)

    # Limpiar y crear de nuevo
    user.delete()

    user = User.objects.create_user(
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )

    print(f"[OK] Usuario creado con create_user()")
    print(f"  Password hash inicial: {user.password[:50]}...")
    print(f"  check_password() ANTES de save(): {check_password(test_password, user.password)}")

    # Simular lo que hace el endpoint: asignar campo y guardar
    user.centro_distribucion_id = None
    password_before_save = user.password
    user.save()  # ESTO CAUSA EL PROBLEMA

    print(f"\n[OK] Despues de user.save():")
    print(f"  Password hash cambio: {password_before_save != user.password}")
    print(f"  Password hash nuevo: {user.password[:50]}...")
    print(f"  check_password() DESPUES de save(): {check_password(test_password, user.password)}")

    # Intentar autenticar después del save
    auth_user = authenticate(email=test_email, password=test_password)
    print(f"  authenticate(): {'[OK] EXITOSO' if auth_user else '[FALLO] FALLO'}")

    print("\n" + "="*60)
    print("PRUEBA 3: Usando update_fields en save()")
    print("="*60)

    # Limpiar y crear de nuevo
    user.delete()

    user = User.objects.create_user(
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )

    print(f"[OK] Usuario creado con create_user()")
    password_before_save = user.password

    # Asignar campo y guardar SOLO ese campo
    user.centro_distribucion_id = None
    user.save(update_fields=['centro_distribucion'])

    print(f"  Password hash cambio: {password_before_save != user.password}")
    print(f"  check_password(): {check_password(test_password, user.password)}")

    # Intentar autenticar
    auth_user = authenticate(email=test_email, password=test_password)
    print(f"  authenticate(): {'[OK] EXITOSO' if auth_user else '[FALLO] FALLO'}")

    # Limpiar
    user.delete()
    print("\n[OK] Usuario de prueba eliminado")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_user_creation()
