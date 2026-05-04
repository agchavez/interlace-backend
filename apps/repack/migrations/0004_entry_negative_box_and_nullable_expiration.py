from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repack', '0003_repackentry_product_to_maintenance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repackentry',
            name='box_count',
            field=models.IntegerField(verbose_name='Cantidad de cajas'),
        ),
        migrations.AlterField(
            model_name='repackentry',
            name='expiration_date',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de vencimiento'),
        ),
    ]
