from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('truck_cycle', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pautamodel',
            name='reentered_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Momento en que la recarga re-ingresó al CD.',
                verbose_name='Re-ingreso',
            ),
        ),
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
        migrations.AlterField(
            model_name='pautatimestampmodel',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('T0_PICKING_START', 'T0 - Inicio de Picking'),
                    ('T1_PICKING_END', 'T1 - Fin de Picking'),
                    ('T1A_YARD_START', 'T1A - Inicio Movimiento a Bahía'),
                    ('T1B_YARD_END', 'T1B - Fin Movimiento a Bahía'),
                    ('T2_BAY_ASSIGNED', 'T2 - Andén Asignado'),
                    ('T3_LOADING_START', 'T3 - Inicio de Carga'),
                    ('T4_LOADING_END', 'T4 - Fin de Carga'),
                    ('T5_COUNT_START', 'T5 - Inicio de Conteo'),
                    ('T6_COUNT_END', 'T6 - Fin de Conteo'),
                    ('T7_CHECKOUT_SECURITY', 'T7 - Checkout Seguridad'),
                    ('T8_CHECKOUT_OPS', 'T8 - Checkout Operaciones'),
                    ('T9_DISPATCH', 'T9 - Despacho'),
                    ('T10_ARRIVAL', 'T10 - Llegada'),
                    ('T10A_RELOAD_REENTRY', 'T10A - Re-ingreso Recarga'),
                    ('T11_RELOAD_QUEUE', 'T11 - Cola de Recarga'),
                    ('T12_RETURN_START', 'T12 - Inicio de Devolución'),
                    ('T13_RETURN_END', 'T13 - Fin de Devolución'),
                    ('T14_AUDIT_START', 'T14 - Inicio de Auditoría'),
                    ('T15_AUDIT_END', 'T15 - Fin de Auditoría'),
                    ('T16_CLOSE', 'T16 - Cierre'),
                    ('T17_CANCELLED', 'T17 - Cancelada'),
                ],
                max_length=30,
                verbose_name='Tipo de Evento',
            ),
        ),
    ]
