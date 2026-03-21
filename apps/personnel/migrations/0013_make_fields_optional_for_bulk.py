import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0012_make_phone_optional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personnelprofile',
            name='first_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nombres'),
        ),
        migrations.AlterField(
            model_name='personnelprofile',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de nacimiento'),
        ),
        migrations.AlterField(
            model_name='personnelprofile',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('M', 'Masculino'), ('F', 'Femenino'), ('OTHER', 'Otro')],
                max_length=10,
                verbose_name='Género',
            ),
        ),
    ]
