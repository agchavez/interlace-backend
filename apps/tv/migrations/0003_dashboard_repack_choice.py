from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tv', '0002_dashboard_role_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tvsession',
            name='dashboard',
            field=models.CharField(
                choices=[
                    ('WORKSTATION',         'Workstation (estaciones de trabajo)'),
                    ('WORKSTATION_PICKING', 'Estación de trabajo del operador · Picking (legacy)'),
                    ('WORKSTATION_PICKER',  'Workstation Picker · KPIs por turno'),
                    ('WORKSTATION_COUNTER', 'Workstation Contador · KPIs por turno'),
                    ('WORKSTATION_YARD',    'Workstation Chofer de Patio · KPIs por turno'),
                    ('WORKSTATION_REPACK',  'Workstation Reempaque · KPIs por turno'),
                ],
                default='WORKSTATION',
                max_length=20,
                verbose_name='Dashboard',
            ),
        ),
    ]
