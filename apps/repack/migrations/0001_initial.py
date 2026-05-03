import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('maintenance',  '__latest__'),
        ('personnel',    '__latest__'),
        ('truck_cycle',  '__latest__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RepackSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('operational_date', models.DateField(db_index=True, verbose_name='Fecha operativa')),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='Inicio')),
                ('ended_at', models.DateTimeField(blank=True, null=True, verbose_name='Fin')),
                ('status', models.CharField(
                    choices=[('ACTIVE', 'Activa'), ('COMPLETED', 'Completada'), ('CANCELLED', 'Cancelada')],
                    default='ACTIVE', max_length=12, verbose_name='Estado',
                )),
                ('notes', models.TextField(blank=True, default='', verbose_name='Notas')),
                ('distributor_center', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='repack_sessions',
                    to='maintenance.distributorcenter',
                    verbose_name='Centro de distribución',
                )),
                ('personnel', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='repack_sessions',
                    to='personnel.personnelprofile',
                    verbose_name='Operario',
                )),
                ('started_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='repack_sessions_started',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Iniciada por',
                )),
            ],
            options={
                'verbose_name': 'Sesión de reempaque',
                'verbose_name_plural': 'Sesiones de reempaque',
                'db_table': 'repack_session',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='RepackEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('material_code', models.CharField(max_length=40, verbose_name='Código de material')),
                ('product_name', models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre del producto')),
                ('box_count', models.PositiveIntegerField(verbose_name='Cantidad de cajas')),
                ('expiration_date', models.DateField(verbose_name='Fecha de vencimiento')),
                ('notes', models.CharField(blank=True, default='', max_length=200, verbose_name='Notas')),
                ('product', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='repack_entries',
                    to='truck_cycle.productcatalogmodel',
                    verbose_name='Producto',
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='entries',
                    to='repack.repacksession',
                    verbose_name='Sesión',
                )),
            ],
            options={
                'verbose_name': 'Entrada de reempaque',
                'verbose_name_plural': 'Entradas de reempaque',
                'db_table': 'repack_entry',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='repacksession',
            index=models.Index(fields=['personnel', '-operational_date'], name='repack_sess_personn_idx'),
        ),
        migrations.AddIndex(
            model_name='repacksession',
            index=models.Index(fields=['distributor_center', '-operational_date', 'status'], name='repack_sess_dc_idx'),
        ),
        migrations.AddIndex(
            model_name='repackentry',
            index=models.Index(fields=['session', '-created_at'], name='repack_entry_sess_idx'),
        ),
        migrations.AddIndex(
            model_name='repackentry',
            index=models.Index(fields=['material_code'], name='repack_entry_mat_idx'),
        ),
        migrations.AddIndex(
            model_name='repackentry',
            index=models.Index(fields=['expiration_date'], name='repack_entry_exp_idx'),
        ),
    ]
