"""
Reabre las bay assignments de pautas que siguen físicamente en la bahía
(estados post-IN_BAY y pre-DISPATCHED) pero cuyo released_at quedó seteado
por el bug anterior en complete_loading.

Uso:
    python manage.py reopen_bay_assignments            # dry-run
    python manage.py reopen_bay_assignments --apply    # aplica cambios
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.truck_cycle.models.core import PautaModel


# Estados donde el camión SIGUE en la bahía físicamente.
IN_BAY_STATUSES = [
    'IN_BAY', 'PENDING_COUNT', 'COUNTING', 'COUNTED',
    'PENDING_CHECKOUT', 'CHECKOUT_SECURITY', 'CHECKOUT_OPS',
]


class Command(BaseCommand):
    help = 'Reabre bay assignments para pautas que siguen en la bahía (bug-fix post complete_loading).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica los cambios. Sin este flag solo hace dry-run.',
        )

    def handle(self, *args, **options):
        # Pautas con estado de "aún en bahía" + bay_assignment liberada.
        pautas = PautaModel.objects.filter(
            status__in=IN_BAY_STATUSES,
            bay_assignment__released_at__isnull=False,
        ).select_related('bay_assignment', 'bay_assignment__bay')

        total = pautas.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No hay bay assignments que reabrir.'))
            return

        self.stdout.write(f'Encontradas {total} pautas con bahía indebidamente liberada:')
        for p in pautas[:20]:
            ba = p.bay_assignment
            self.stdout.write(
                f'  T-{p.transport_number} · {p.status} · Bahía {ba.bay.code} '
                f'(liberada en {ba.released_at.isoformat() if ba.released_at else "-"})'
            )
        if total > 20:
            self.stdout.write(f'  ... y {total - 20} más.')

        if not options['apply']:
            self.stdout.write(self.style.NOTICE('Dry-run. Usa --apply para reabrir.'))
            return

        with transaction.atomic():
            from apps.truck_cycle.models.operational import PautaBayAssignmentModel
            updated = PautaBayAssignmentModel.objects.filter(
                pauta__in=pautas,
            ).update(released_at=None)

        self.stdout.write(self.style.SUCCESS(
            f'Reabiertas {updated} bay assignments. Ahora las pautas vuelven a verse en el mapa del estacionamiento.'
        ))
