from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workstation', '0002_workstationblock_workstationimage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workstation',
            name='role',
            field=models.CharField(
                choices=[
                    ('PICKING', 'Picking (legacy)'),
                    ('PICKER', 'Picker'),
                    ('COUNTER', 'Contador'),
                    ('YARD', 'Chofer de Patio'),
                    ('REPACK', 'Reempaque'),
                ],
                max_length=10,
                verbose_name='Rol',
            ),
        ),
    ]
