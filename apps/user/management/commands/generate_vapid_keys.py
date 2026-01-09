"""
Management command para generar llaves VAPID para Web Push Notifications
"""
from django.core.management.base import BaseCommand
from django.core.management import CommandError


class Command(BaseCommand):
    help = 'Genera llaves VAPID (Voluntary Application Server Identification) para Web Push'

    def handle(self, *args, **options):
        try:
            from pywebpush import webpush
            from py_vapid import Vapid01 as Vapid
        except ImportError:
            raise CommandError(
                'pywebpush y py-vapid no están instalados.\n'
                'Instálalos con: pip install pywebpush py-vapid'
            )

        import base64
        from cryptography.hazmat.primitives import serialization

        self.stdout.write('\nGenerando llaves VAPID...\n')

        # Generar llaves VAPID
        vapid = Vapid()
        vapid.generate_keys()

        # Obtener las llaves en formato base64 URL-safe
        # Private key en formato PEM
        private_pem = vapid.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Public key en formato base64 URL-safe (como espera el navegador)
        public_raw = vapid.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_key = base64.urlsafe_b64encode(public_raw).decode('utf-8').rstrip('=')

        private_key = private_pem.decode('utf-8')

        # Mostrar las llaves
        self.stdout.write(self.style.SUCCESS('\nLlaves VAPID generadas exitosamente!\n'))

        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('IMPORTANTE: Guarda estas llaves en tu archivo .env'))
        self.stdout.write(self.style.WARNING('=' * 80))

        self.stdout.write('\n# Agrega estas líneas a tu archivo .env del backend:\n')
        self.stdout.write(f'VAPID_PRIVATE_KEY={private_key}')
        self.stdout.write(f'VAPID_PUBLIC_KEY={public_key}')
        self.stdout.write('VAPID_ADMIN_EMAIL=admin@tracker.alt  # Cambia esto por tu email')

        self.stdout.write('\n# Agrega esta línea a tu archivo .env del frontend:\n')
        self.stdout.write(f'VITE_VAPID_PUBLIC_KEY={public_key}')

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('ADVERTENCIA: NO compartas la llave privada (VAPID_PRIVATE_KEY)'))
        self.stdout.write(self.style.WARNING('La llave publica puede ser compartida con el frontend'))
        self.stdout.write('=' * 80 + '\n')

        # Guardar en archivos de ejemplo
        try:
            with open('.env.vapid.example', 'w') as f:
                f.write('# Backend VAPID Configuration\n')
                f.write(f'VAPID_PRIVATE_KEY={private_key}\n')
                f.write(f'VAPID_PUBLIC_KEY={public_key}\n')
                f.write('VAPID_ADMIN_EMAIL=admin@tracker.alt\n')

            self.stdout.write(self.style.SUCCESS('Archivo .env.vapid.example creado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear archivo .env.vapid.example: {e}'))

        self.stdout.write('')
