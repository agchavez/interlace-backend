import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0011_remove_size_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personnelprofile',
            name='phone',
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[
                    django.core.validators.RegexValidator(
                        message='Número de teléfono inválido',
                        regex='^\\+?[\\d\\s\\-\\(\\)]+$',
                    )
                ],
                verbose_name='Teléfono',
            ),
        ),
    ]
