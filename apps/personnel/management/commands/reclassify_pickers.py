"""
Reclasifica al personal con `position_type=LOADER` y puesto 'AYUDANTE DE RUTA'
a `position_type=PICKER` con puesto 'Picker', que es el rol real que cumplen
en la operación de ciclo del camión.

Uso:
    python manage.py reclassify_pickers            # dry-run (solo muestra)
    python manage.py reclassify_pickers --apply    # aplica los cambios
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.personnel.models.personnel import PersonnelProfile


TARGET_POSITION_TEXT = 'AYUDANTE DE RUTA'
NEW_POSITION_TEXT = 'Picker'


class Command(BaseCommand):
    help = 'Reclasifica LOADER / AYUDANTE DE RUTA → PICKER / Picker.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica los cambios. Sin este flag solo hace dry-run.',
        )

    def handle(self, *args, **options):
        qs = PersonnelProfile.objects.filter(
            position_type=PersonnelProfile.LOADER,
            position__iexact=TARGET_POSITION_TEXT,
        )
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.WARNING(
                f'No se encontró personal con position_type=LOADER y position="{TARGET_POSITION_TEXT}".'
            ))
            return

        self.stdout.write(
            f'Encontrados {total} registros con position_type=LOADER y "{TARGET_POSITION_TEXT}".'
        )

        if not options['apply']:
            self.stdout.write(self.style.NOTICE('Dry-run. Usa --apply para aplicar cambios.'))
            # Muestra los primeros 10
            for p in qs.order_by('employee_code')[:10]:
                self.stdout.write(f'  {p.employee_code} — {p.first_name} {p.last_name}')
            if total > 10:
                self.stdout.write(f'  ... y {total - 10} más.')
            return

        with transaction.atomic():
            updated = qs.update(
                position_type=PersonnelProfile.PICKER,
                position=NEW_POSITION_TEXT,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Reclasificados {updated} registros a position_type=PICKER, position="{NEW_POSITION_TEXT}".'
        ))
