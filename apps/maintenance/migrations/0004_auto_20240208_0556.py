from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0003_alter_productmodel_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputtypemodel',
            name='required_orders',
            field=models.BooleanField(default=False, verbose_name='Requiere pedidos'),
        ),
        migrations.AlterField(
            model_name='operatormodel',
            name='first_name',
            field=models.CharField(max_length=60, verbose_name='Nombre'),
        ),
        migrations.AlterField(
            model_name='operatormodel',
            name='last_name',
            field=models.CharField(max_length=60, verbose_name='Apellido'),
        ),
        migrations.CreateModel(
            name='LotModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('code', models.CharField(max_length=6, verbose_name='Código')),
                ('distributor_center', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='maintenance.distributorcenter', verbose_name='Centro de Distribución')),
            ],
            options={
                'verbose_name': 'Lote',
                'verbose_name_plural': 'Lotes',
                'db_table': 'lot',
                'unique_together': {('distributor_center', 'code')},
            },
        ),
    ]
