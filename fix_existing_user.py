"""
Script para arreglar usuarios existentes con contraseñas hasheadas incorrectamente
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

def fix_user_password(email, new_password):
    """Arregla la contraseña de un usuario existente"""

    try:
        user = User.objects.get(email=email)
        print(f"\n[OK] Usuario encontrado: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Password hash actual: {user.password[:50]}...")
        print(f"  Password es valido: {check_password(new_password, user.password)}")

        # Usar set_password para hashear correctamente
        print(f"\n[INFO] Actualizando contrasena a: {new_password}")
        user.set_password(new_password)
        user.save()

        print(f"  Nuevo password hash: {user.password[:50]}...")
        print(f"  check_password(): {check_password(new_password, user.password)}")

        # Intentar autenticar
        auth_user = authenticate(email=email, password=new_password)
        if auth_user:
            print(f"\n[OK] AUTENTICACION EXITOSA")
            print(f"  User ID: {auth_user.id}")
            print(f"  Email: {auth_user.email}")
            print(f"  Is active: {auth_user.is_active}")
        else:
            print(f"\n[ERROR] AUTENTICACION FALLO")

        return True

    except User.DoesNotExist:
        print(f"\n[ERROR] Usuario con email {email} no encontrado")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        return False

if __name__ == "__main__":
    # Usuario a arreglar
    email = "pruebachavez@unah.hn"
    password = "Chavez_325AC"

    print("="*60)
    print("SCRIPT PARA ARREGLAR CONTRASEÑA DE USUARIO")
    print("="*60)

    fix_user_password(email, password)

    print("\n" + "="*60)
