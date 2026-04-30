from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workstation', '0003_add_repack_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workstationblock',
            name='type',
            field=models.CharField(
                choices=[
                    ('RISKS', 'Riesgos del área'),
                    ('PROHIBITIONS', 'Prohibiciones del área'),
                    ('TRIGGERS', 'Disparador resolución de problemas'),
                    ('SIC_CHART', 'SIC / Pi Crítico'),
                    ('REACTION_PLANS', 'Planes de Reacción'),
                    ('PERFORMERS', 'Top / Bottom Performers'),
                    ('QR_DOCUMENT', 'QR · Documento PDF'),
                    ('QR_EXTERNAL', 'QR · Link externo'),
                    ('IMAGE', 'Imagen'),
                    ('TEXT', 'Texto / Nota'),
                    ('TITLE', 'Título'),
                    ('CLOCK', 'Reloj'),
                    ('DPO', 'Sello DPO'),
                ],
                max_length=20,
                verbose_name='Tipo',
            ),
        ),
    ]
