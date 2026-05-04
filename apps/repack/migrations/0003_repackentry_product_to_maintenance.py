"""
RepackEntry.product ahora apunta a maintenance.ProductModel (catálogo
visible para el usuario) en lugar de truck_cycle.ProductCatalogModel.

El campo es nullable, así que no requiere data migration — los registros
existentes con product=NULL quedan iguales y los que tuvieran un FK
inválido se nulean al cambiar el FK.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '__latest__'),
        ('repack', '0002_rename_repack_entry_sess_idx_repack_entr_session_4dc58f_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repackentry',
            name='product',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='repack_entries',
                to='maintenance.productmodel',
                verbose_name='Producto',
            ),
        ),
    ]
