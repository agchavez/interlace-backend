from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0010_add_certification_status_and_signature'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personnelprofile',
            name='shirt_size',
            field=models.CharField(blank=True, max_length=10, verbose_name='Talla de camisa'),
        ),
        migrations.AlterField(
            model_name='personnelprofile',
            name='glove_size',
            field=models.CharField(blank=True, max_length=10, verbose_name='Talla de guantes'),
        ),
        migrations.AlterField(
            model_name='personnelprofile',
            name='helmet_size',
            field=models.CharField(blank=True, max_length=10, verbose_name='Talla de casco'),
        ),
    ]
