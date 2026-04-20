"""
Resetea las pautas del día operativo (hoy por defecto) al estado inicial
PENDING_PICKING para poder probar el flujo desde cero.

Qué borra por pauta:
    - timestamps
    - assignments
    - bay_assignments
    - inconsistencies
    - photos
    - checkout_validation
    - pallet_tickets
    - reentered_at (lo limpia)

Qué preserva:
    - La pauta misma, su camión, ruta, productos, deliveries, totales, is_reload
    - Las subidas (PalletComplexUpload)

Ejecutar:
    python manage.py reset_today_pautas              # hoy
    python manage.py reset_today_pautas --date 2026-04-19
    python manage.py reset_today_pautas --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.truck_cycle.models.core import PautaModel


class Command(BaseCommand):
    help = "Resetea las pautas del día a PENDING_PICKING y limpia timestamps/asignaciones."

    def add_arguments(self, parser):
        parser.add_argument('--date', help='YYYY-MM-DD (default: hoy)')
        parser.add_argument('--dry-run', action='store_true', help='No escribir cambios')

    def handle(self, *args, **options):
        op_date = options.get('date') or timezone.localdate().isoformat()
        dry = options.get('dry_run', False)

        qs = PautaModel.objects.filter(operational_date=op_date)
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(f"No hay pautas con operational_date={op_date}."))
            return

        self.stdout.write(self.style.NOTICE(
            f"{'[DRY RUN] ' if dry else ''}Reseteando {count} pauta(s) de {op_date}..."
        ))

        if dry:
            for p in qs:
                self.stdout.write(f"  - T-{p.transport_number} (status={p.status}, reload={p.is_reload})")
            return

        with transaction.atomic():
            for p in qs:
                p.timestamps.all().delete()
                p.assignments.all().delete()
                p.inconsistencies.all().delete()
                p.photos.all().delete()
                p.pallet_tickets.all().delete()
                if hasattr(p, 'bay_assignment') and p.bay_assignment:
                    p.bay_assignment.delete()
                if hasattr(p, 'checkout_validation') and p.checkout_validation:
                    p.checkout_validation.delete()

                p.status = 'PENDING_PICKING'
                p.reentered_at = None
                p.save(update_fields=['status', 'reentered_at'])

                self.stdout.write(f"  ✓ T-{p.transport_number} reseteada")

        self.stdout.write(self.style.SUCCESS(
            f"Listo. {count} pauta(s) vueltas a PENDING_PICKING."
        ))
