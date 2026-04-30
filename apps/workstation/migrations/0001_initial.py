import uuid

import apps.workstation.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('maintenance', '0006_distributorcenter_location_city_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiskCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=40, unique=True, verbose_name='Código')),
                ('name', models.CharField(max_length=80, verbose_name='Nombre')),
                ('icon_name', models.CharField(help_text='Nombre del ícono MUI, ej: DirectionsRun, ContentCut', max_length=60, verbose_name='Ícono Material UI')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Catálogo · Riesgo',
                'verbose_name_plural': 'Catálogo · Riesgos',
                'db_table': 'workstation_risk_catalog',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProhibitionCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=40, unique=True, verbose_name='Código')),
                ('name', models.CharField(max_length=80, verbose_name='Nombre')),
                ('icon_name', models.CharField(help_text='Nombre del ícono MUI, ej: Fastfood, SmokingRooms', max_length=60, verbose_name='Ícono Material UI')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Catálogo · Prohibición',
                'verbose_name_plural': 'Catálogo · Prohibiciones',
                'db_table': 'workstation_prohibition_catalog',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Workstation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('role', models.CharField(choices=[('PICKING', 'Picking (legacy)'), ('PICKER', 'Picker'), ('COUNTER', 'Contador'), ('YARD', 'Chofer de Patio')], max_length=10, verbose_name='Rol')),
                ('name', models.CharField(blank=True, default='', max_length=80, verbose_name='Nombre')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('distributor_center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workstations', to='maintenance.distributorcenter', verbose_name='Centro de Distribución')),
            ],
            options={
                'verbose_name': 'Estación de Trabajo',
                'verbose_name_plural': 'Estaciones de Trabajo',
                'db_table': 'workstation',
                'ordering': ['distributor_center__name', 'role'],
                'unique_together': {('distributor_center', 'role')},
            },
        ),
        migrations.CreateModel(
            name='WorkstationRisk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('risk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='workstation.riskcatalog')),
                ('workstation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risks', to='workstation.workstation')),
            ],
            options={
                'verbose_name': 'Riesgo de Estación',
                'verbose_name_plural': 'Riesgos de Estación',
                'db_table': 'workstation_risk',
                'ordering': ['display_order', 'risk__name'],
                'unique_together': {('workstation', 'risk')},
            },
        ),
        migrations.CreateModel(
            name='WorkstationProhibition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('prohibition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='workstation.prohibitioncatalog')),
                ('workstation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prohibitions', to='workstation.workstation')),
            ],
            options={
                'verbose_name': 'Prohibición de Estación',
                'verbose_name_plural': 'Prohibiciones de Estación',
                'db_table': 'workstation_prohibition',
                'ordering': ['display_order', 'prohibition__name'],
                'unique_together': {('workstation', 'prohibition')},
            },
        ),
        migrations.CreateModel(
            name='Trigger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('indicator', models.CharField(max_length=120, verbose_name='Indicador')),
                ('unit', models.CharField(blank=True, default='', max_length=40, verbose_name='Unidad')),
                ('goal', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Meta')),
                ('trigger_5pq', models.DecimalField(decimal_places=2, help_text='Valor a partir del cual se ejecuta el 5 Porqué', max_digits=12, verbose_name='Disparador 5 Porqué')),
                ('trigger_ra', models.DecimalField(decimal_places=2, help_text='Valor a partir del cual se ejecuta el Relato de Anomalía', max_digits=12, verbose_name='Disparador Relato de Anomalía')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('workstation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='triggers', to='workstation.workstation')),
            ],
            options={
                'verbose_name': 'Disparador / Meta',
                'verbose_name_plural': 'Disparadores / Metas',
                'db_table': 'workstation_trigger',
                'ordering': ['workstation', 'display_order'],
            },
        ),
        migrations.CreateModel(
            name='ReactionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('zone', models.CharField(choices=[('YELLOW', 'Zona Amarilla · 5 Porqué'), ('RED', 'Zona Roja · Relato de Anomalía')], max_length=8, verbose_name='Zona')),
                ('title', models.CharField(max_length=160, verbose_name='Título')),
                ('description', models.TextField(verbose_name='Descripción')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('trigger', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reaction_plans', to='workstation.trigger', verbose_name='Indicador asociado')),
                ('workstation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reaction_plans', to='workstation.workstation')),
            ],
            options={
                'verbose_name': 'Plan de Reacción',
                'verbose_name_plural': 'Planes de Reacción',
                'db_table': 'workstation_reaction_plan',
                'ordering': ['workstation', 'zone', 'display_order'],
            },
        ),
        migrations.CreateModel(
            name='WorkstationDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro')),
                ('doc_type', models.CharField(choices=[('SOP', 'SOP — Standard Operating Procedure'), ('OPL', 'OPL — One Point Lesson'), ('OTHER', 'Otro')], max_length=10, verbose_name='Tipo')),
                ('name', models.CharField(max_length=160, verbose_name='Nombre')),
                ('file', models.FileField(upload_to=apps.workstation.models.workstation_doc_upload_path, verbose_name='Archivo PDF')),
                ('qr_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Token QR')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('workstation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='workstation.workstation')),
            ],
            options={
                'verbose_name': 'Documento de Estación',
                'verbose_name_plural': 'Documentos de Estación',
                'db_table': 'workstation_document',
                'ordering': ['workstation', 'doc_type', 'display_order'],
            },
        ),
    ]
