"""
Comando para crear tipos de certificación de ejemplo
"""
from django.core.management.base import BaseCommand
from apps.personnel.models import CertificationType


class Command(BaseCommand):
    help = 'Crea tipos de certificación de ejemplo'

    def handle(self, *args, **options):
        certification_types = [
            {
                'code': 'ETICA-COMP',
                'name': 'Entrenamiento Anual de Etica y Compliance',
                'description': 'Entrenamiento anual obligatorio sobre ética empresarial y cumplimiento normativo',
                'validity_period_days': 365,
                'requires_renewal': True,
                'is_mandatory': True,
            },
            {
                'code': 'MONT',
                'name': 'Certificación de Montacargas',
                'description': 'Certificación para operar montacargas',
                'validity_period_days': 365,
                'requires_renewal': True,
                'is_mandatory': True,
            },
            {
                'code': 'SEG-IND',
                'name': 'Seguridad Industrial',
                'description': 'Certificación en seguridad industrial',
                'validity_period_days': 730,
                'requires_renewal': True,
                'is_mandatory': True,
            },
            {
                'code': 'PRIM-AUX',
                'name': 'Primeros Auxilios',
                'description': 'Certificación en primeros auxilios básicos',
                'validity_period_days': 365,
                'requires_renewal': True,
                'is_mandatory': False,
            },
            {
                'code': 'MANIP-ALI',
                'name': 'Manipulación de Alimentos',
                'description': 'Certificación para manipulación de alimentos',
                'validity_period_days': 180,
                'requires_renewal': True,
                'is_mandatory': False,
            },
            {
                'code': 'PREV-INC',
                'name': 'Prevención de Incendios',
                'description': 'Certificación en prevención y combate de incendios',
                'validity_period_days': 365,
                'requires_renewal': True,
                'is_mandatory': True,
            },
            {
                'code': 'ALMAC',
                'name': 'Gestión de Almacenes',
                'description': 'Certificación en gestión y operación de almacenes',
                'validity_period_days': 730,
                'requires_renewal': False,
                'is_mandatory': False,
            },
            {
                'code': 'INV',
                'name': 'Control de Inventarios',
                'description': 'Certificación en control y gestión de inventarios',
                'validity_period_days': 365,
                'requires_renewal': False,
                'is_mandatory': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for cert_data in certification_types:
            cert_type, created = CertificationType.objects.update_or_create(
                code=cert_data['code'],
                defaults=cert_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {cert_type.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'• Actualizado: {cert_type.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Proceso completado: {created_count} creados, {updated_count} actualizados'
            )
        )
