from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0016_rename_metric_sample_person_idx_app_personn_personn_95a825_idx_and_more'),
        ('repack', '0004_entry_negative_box_and_nullable_expiration'),
    ]

    operations = [
        migrations.AddField(
            model_name='repacksession',
            name='supervisor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='repack_sessions_supervised',
                to='personnel.personnelprofile',
                verbose_name='Supervisor del turno',
            ),
        ),
        migrations.AddField(
            model_name='repacksession',
            name='helpers',
            field=models.ManyToManyField(
                blank=True,
                related_name='repack_sessions_helped',
                to='personnel.personnelprofile',
                verbose_name='Ayudantes del turno',
            ),
        ),
    ]
