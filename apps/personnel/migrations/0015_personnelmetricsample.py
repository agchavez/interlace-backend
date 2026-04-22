from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0014_alter_personnelprofile_position_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonnelMetricSample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operational_date', models.DateField(db_index=True, verbose_name='Fecha operativa')),
                ('numeric_value', models.DecimalField(decimal_places=4, max_digits=12, verbose_name='Valor')),
                ('source', models.CharField(choices=[('AUTO_TRUCK_CYCLE', 'Auto - Truck Cycle'), ('MANUAL', 'Manual')], default='AUTO_TRUCK_CYCLE', max_length=30, verbose_name='Origen')),
                ('pauta_id', models.IntegerField(blank=True, db_index=True, null=True, verbose_name='Pauta id')),
                ('context', models.JSONField(blank=True, default=dict, verbose_name='Contexto')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metric_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='samples', to='personnel.performancemetrictype', verbose_name='Tipo de métrica')),
                ('personnel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metric_samples', to='personnel.personnelprofile', verbose_name='Personal')),
            ],
            options={
                'verbose_name': 'Sample de métrica',
                'verbose_name_plural': 'Samples de métricas',
                'db_table': 'app_personnel_metric_sample',
                'ordering': ['-operational_date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='personnelmetricsample',
            index=models.Index(fields=['personnel', '-operational_date'], name='metric_sample_person_idx'),
        ),
        migrations.AddIndex(
            model_name='personnelmetricsample',
            index=models.Index(fields=['metric_type', '-operational_date'], name='metric_sample_type_idx'),
        ),
        migrations.AddIndex(
            model_name='personnelmetricsample',
            index=models.Index(fields=['operational_date'], name='metric_sample_date_idx'),
        ),
        migrations.AddIndex(
            model_name='personnelmetricsample',
            index=models.Index(fields=['pauta_id', 'metric_type'], name='metric_sample_pauta_idx'),
        ),
    ]
