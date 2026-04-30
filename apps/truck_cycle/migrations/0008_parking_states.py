from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('truck_cycle', '0007_kpitarget_metric_direction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pautamodel',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_PICKING', 'Pendiente de Picking'),
                    ('PICKING_ASSIGNED', 'Picking Asignado'),
                    ('PICKING_IN_PROGRESS', 'Picking en Progreso'),
                    ('PICKING_DONE', 'Picking Completado'),
                    ('MOVING_TO_BAY', 'Moviéndose a Bahía'),
                    ('IN_BAY', 'En Andén'),
                    ('PENDING_COUNT', 'Pendiente de Conteo'),
                    ('COUNTING', 'Contando'),
                    ('COUNTED', 'Contado'),
                    ('MOVING_TO_PARKING', 'Moviéndose a Estacionamiento'),
                    ('PARKED', 'Estacionado'),
                    ('PENDING_CHECKOUT', 'Pendiente de Checkout'),
                    ('CHECKOUT_SECURITY', 'Checkout Seguridad'),
                    ('CHECKOUT_OPS', 'Checkout Operaciones'),
                    ('DISPATCHED', 'Despachado'),
                    ('IN_RELOAD_QUEUE', 'En Cola de Recarga'),
                    ('PENDING_RETURN', 'Pendiente de Devolución'),
                    ('RETURN_PROCESSED', 'Devolución Procesada'),
                    ('IN_AUDIT', 'En Auditoría'),
                    ('AUDIT_COMPLETE', 'Auditoría Completa'),
                    ('CLOSED', 'Cerrada'),
                    ('CANCELLED', 'Cancelada'),
                ],
                default='PENDING_PICKING',
                max_length=30,
                verbose_name='Estado',
            ),
        ),
        migrations.AddField(
            model_name='checkoutvalidationmodel',
            name='dispatched_without_security',
            field=models.BooleanField(
                default=False,
                verbose_name='Despachado sin Validación de Seguridad',
            ),
        ),
    ]
