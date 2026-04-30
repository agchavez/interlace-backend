"""
Bootstrap completo del módulo Workstation.

Combina los pasos de carga inicial en un solo comando, ideal para usar
después de un deploy o al instalar el módulo en un entorno nuevo:

  1. seed_workstation_catalogs  — Riesgos + Prohibiciones master.
  2. ensure_workstations        — Crea (CD, rol) faltantes con template
                                  default (precarga riesgos, prohibiciones,
                                  disparadores y SIC con los KPIs vigentes
                                  del CD).

Flags:
  --reset-empty   Re-aplica el template en workstations existentes que NO
                  tengan bloques (útil tras introducir el módulo).
  --force-reset   Borra TODOS los bloques de TODAS las workstations y
                  re-aplica el template. ⚠ Destructivo — pide confirmación.

Ejemplos:
  python manage.py bootstrap_workstations
  python manage.py bootstrap_workstations --reset-empty
  python manage.py bootstrap_workstations --force-reset --noinput
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.maintenance.models.distributor_center import DistributorCenter
from apps.workstation.models import Workstation, WorkstationBlock
from apps.workstation.templates import apply_default_template


class Command(BaseCommand):
    help = 'Bootstrap del módulo Workstation: catálogos + estaciones precargadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-empty', action='store_true',
            help='Re-aplica el template en workstations existentes sin bloques.',
        )
        parser.add_argument(
            '--force-reset', action='store_true',
            help='Borra todos los bloques y re-aplica el template a TODAS las workstations.',
        )
        parser.add_argument(
            '--noinput', action='store_true',
            help='No pedir confirmación en operaciones destructivas.',
        )
        parser.add_argument(
            '--skip-catalogs', action='store_true',
            help='Saltar la carga de catálogos master (Riesgos/Prohibiciones).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('BOOTSTRAP WORKSTATIONS'))
        self.stdout.write(self.style.WARNING('=' * 60))

        # 1) Catálogos master
        if not options['skip_catalogs']:
            self.stdout.write('\n[1/2] Cargando catálogos master…')
            call_command('seed_workstation_catalogs')
        else:
            self.stdout.write('\n[1/2] Catálogos master: omitido (--skip-catalogs).')

        # 2) Estaciones por (CD, rol)
        self.stdout.write('\n[2/2] Creando/asegurando workstations…')

        if options['force_reset']:
            self._force_reset(noinput=options['noinput'])
        else:
            call_command(
                'ensure_workstations',
                **{'reapply_empty': options['reset_empty']},
            )

        self.stdout.write(self.style.SUCCESS('\n[✓] Bootstrap completado.'))

    def _force_reset(self, noinput: bool):
        total_dcs = DistributorCenter.objects.count()
        total_ws = Workstation.objects.count()
        if not noinput:
            self.stdout.write(self.style.ERROR(
                f'\n⚠  Esto borrará los bloques de las {total_ws} workstations '
                f'existentes (en {total_dcs} CDs) y re-aplicará el template.'
            ))
            self.stdout.write('   Ningún Risk/Prohibition catalog se ve afectado.')
            confirm = input('   Escribí "RESET" para continuar: ')
            if confirm.strip() != 'RESET':
                self.stdout.write(self.style.WARNING('Cancelado.'))
                return

        roles = [r for r, _ in Workstation.ROLE_CHOICES]
        with transaction.atomic():
            for dc in DistributorCenter.objects.all():
                self.stdout.write(self.style.WARNING(f'\n=== {dc.name} ==='))
                for role in roles:
                    ws, was_created = Workstation.objects.get_or_create(
                        distributor_center=dc,
                        role=role,
                        defaults={'is_active': True, 'name': ''},
                    )
                    WorkstationBlock.objects.filter(workstation=ws).delete()
                    apply_default_template(ws)
                    tag = '[+]' if was_created else '[~]'
                    self.stdout.write(self.style.SUCCESS(
                        f'  {tag} {role:<10} template re-aplicado'
                    ))
