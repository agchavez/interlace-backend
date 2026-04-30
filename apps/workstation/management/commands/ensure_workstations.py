"""
Crea un Workstation con template default para cada (CD, rol) que no exista.

- Si la estación no existe → la crea + aplica el template default.
- Si existe pero está vacía (sin bloques) → aplica el template.
- Si existe y ya tiene bloques → no toca nada (respeta lo configurado).

Idempotente: se puede correr múltiples veces sin riesgo. Útil al agregar un CD
nuevo, o tras instalar el módulo en un entorno con CDs ya existentes.

Ejecutar: python manage.py ensure_workstations
"""
from django.core.management.base import BaseCommand

from apps.maintenance.models.distributor_center import DistributorCenter
from apps.workstation.models import Workstation
from apps.workstation.templates import apply_default_template


class Command(BaseCommand):
    help = 'Crea Workstations default para cada (CD, rol) si no existen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reapply-empty',
            action='store_true',
            help='Re-aplica el template a workstations existentes sin bloques.',
        )

    def handle(self, *args, **options):
        reapply_empty = options['reapply_empty']

        dcs = list(DistributorCenter.objects.all())
        if not dcs:
            self.stdout.write(self.style.WARNING('No hay Centros de Distribución cargados.'))
            return

        roles = [r for r, _ in Workstation.ROLE_CHOICES]

        created = filled = skipped = 0
        for dc in dcs:
            self.stdout.write(self.style.WARNING(f'\n=== {dc.name} ==='))
            for role in roles:
                ws, was_created = Workstation.objects.get_or_create(
                    distributor_center=dc,
                    role=role,
                    defaults={'is_active': True, 'name': ''},
                )
                if was_created:
                    apply_default_template(ws)
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'  [+] {role:<10} creada con template'))
                elif reapply_empty and not ws.blocks.exists():
                    apply_default_template(ws)
                    filled += 1
                    self.stdout.write(f'  [~] {role:<10} existente vacía · template aplicado')
                else:
                    skipped += 1
                    self.stdout.write(f'  [=] {role:<10} ya existe ({ws.blocks.count()} bloques)')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(
            f'\nResumen: {created} creadas · {filled} re-llenadas · {skipped} sin tocar.\n'
        ))
