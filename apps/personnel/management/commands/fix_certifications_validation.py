"""
Comando para actualizar el estado de validación de las certificaciones.

Este comando recorre todas las certificaciones existentes y actualiza su campo
is_valid basándose en la lógica correcta:
- Si está revocada -> is_valid = False
- Si ya expiró -> is_valid = False
- Si no está revocada y no ha expirado -> is_valid = True
"""
from django.core.management.base import BaseCommand
from apps.personnel.models.certification import Certification
from datetime import date


class Command(BaseCommand):
    help = 'Actualiza el estado de validación de todas las certificaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la actualización sin guardar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING(
            'Iniciando actualización de certificaciones...\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios\n'))

        # Obtener todas las certificaciones
        certifications = Certification.objects.all()
        total = certifications.count()

        self.stdout.write(f'Encontradas {total} certificaciones\n')

        updated_count = 0
        revoked_count = 0
        expired_count = 0
        valid_count = 0

        today = date.today()

        for cert in certifications:
            old_status = cert.is_valid
            new_status = None
            reason = ""

            # Aplicar la nueva lógica
            if cert.revoked:
                new_status = False
                reason = "Revocada"
                revoked_count += 1
            elif cert.expiration_date < today:
                new_status = False
                reason = "Expirada"
                expired_count += 1
            else:
                new_status = True
                reason = "Válida"
                valid_count += 1

            # Si el estado cambió, actualizarlo
            if old_status != new_status:
                if not dry_run:
                    cert.is_valid = new_status
                    cert.save()

                updated_count += 1
                self.stdout.write(
                    f'  - {cert.personnel.employee_code} | '
                    f'{cert.certification_type.name} | '
                    f'Vence: {cert.expiration_date} | '
                    f'{old_status} -> {new_status} ({reason})'
                )

        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\nRESUMEN:'))
        self.stdout.write(f'  Total de certificaciones: {total}')
        self.stdout.write(f'  Actualizadas: {updated_count}')
        self.stdout.write(f'  - Revocadas: {revoked_count}')
        self.stdout.write(f'  - Expiradas: {expired_count}')
        self.stdout.write(f'  - Válidas: {valid_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nMODO DRY-RUN: Para aplicar los cambios ejecute sin --dry-run'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n¡Actualización completada exitosamente!'))
