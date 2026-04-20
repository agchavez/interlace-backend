"""
Crea los grupos de Django para los roles del Ciclo del Camión, les asigna
permisos personalizados y opcionalmente inscribe a los usuarios con perfil de
personal en el grupo que corresponda según su position_type.

Grupos:
    Picker              — acceso a /work/picker
    Contador            — acceso a /work/counter
    Seguridad Ciclo     — acceso a /work/security
    Operaciones Ciclo   — acceso a /work/ops
    Chofer de Patio     — acceso a /work/yard
    Chofer Vendedor     — acceso a /work/vendor

Ejecutar:
    python manage.py setup_work_groups              # crea grupos e inscribe usuarios
    python manage.py setup_work_groups --skip-enroll  # solo crea grupos/permisos
    python manage.py setup_work_groups --dry-run      # no escribe cambios
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.truck_cycle.models.operational import PautaAssignmentModel


WORK_GROUPS = [
    {
        'name': 'Picker',
        'permission': ('access_work_picker', 'Puede acceder a la pantalla de trabajo de Picker'),
        'home': '/work/picker',
    },
    {
        'name': 'Contador',
        'permission': ('access_work_counter', 'Puede acceder a la pantalla de trabajo de Contador'),
        'home': '/work/counter',
    },
    {
        'name': 'Seguridad Ciclo',
        'permission': ('access_work_security', 'Puede acceder a la pantalla de trabajo de Seguridad'),
        'home': '/work/security',
    },
    {
        'name': 'Operaciones Ciclo',
        'permission': ('access_work_ops', 'Puede acceder a la pantalla de trabajo de Operaciones'),
        'home': '/work/ops',
    },
    {
        'name': 'Chofer de Patio',
        'permission': ('access_work_yard', 'Puede acceder a la pantalla de trabajo de Chofer de Patio'),
        'home': '/work/yard',
    },
    {
        'name': 'Chofer Vendedor',
        'permission': ('access_work_vendor', 'Puede acceder a la pantalla de trabajo de Chofer Vendedor'),
        'home': '/work/vendor',
    },
]

# Migración: nombres viejos → nombres nuevos. Si existe un grupo con el nombre
# viejo se renombra (preservando miembros) en vez de crear uno nuevo.
GROUP_RENAMES = {
    'CICLO_PICKER':          'Picker',
    'CICLO_CONTADOR':        'Contador',
    'CICLO_SEGURIDAD':       'Seguridad Ciclo',
    'CICLO_OPERACIONES':     'Operaciones Ciclo',
    'CICLO_CHOFER_PATIO':    'Chofer de Patio',
    'CICLO_CHOFER_VENDEDOR': 'Chofer Vendedor',
}

# position_type del PersonnelProfile → nombre del grupo.
# Debe quedar alineado con POSITION_TYPE_TO_ROLE del frontend (workRole.ts).
POSITION_TYPE_TO_GROUP = {
    'PICKER':              'Picker',
    'LOADER':              'Picker',
    'COUNTER':             'Contador',
    'WAREHOUSE_ASSISTANT': 'Contador',
    'SECURITY_GUARD':      'Seguridad Ciclo',
    'YARD_DRIVER':         'Chofer de Patio',
    'DELIVERY_DRIVER':     'Chofer Vendedor',
}


class Command(BaseCommand):
    help = "Crea grupos y permisos /work/* e inscribe usuarios según su position_type."

    def add_arguments(self, parser):
        parser.add_argument('--skip-enroll', action='store_true', help='Solo crear grupos/permisos; no inscribir usuarios.')
        parser.add_argument('--dry-run', action='store_true', help='No escribir cambios.')

    def handle(self, *args, **options):
        skip_enroll = options.get('skip_enroll', False)
        dry = options.get('dry_run', False)

        if dry:
            self.stdout.write(self.style.NOTICE('[DRY RUN] no se escribirán cambios.'))

        with transaction.atomic():
            self._rename_legacy_groups(dry)
            self._setup_groups(dry)
            if not skip_enroll:
                self._enroll_users(dry)

            if dry:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("Listo."))

    def _rename_legacy_groups(self, dry: bool) -> None:
        """Renombra grupos viejos CICLO_* si existen, preservando miembros y permisos."""
        renamed: list[tuple[str, str]] = []
        for old, new in GROUP_RENAMES.items():
            legacy = Group.objects.filter(name=old).first()
            if not legacy:
                continue
            # Si ya existe el nuevo, mergeamos: mover miembros y permisos, borrar el viejo.
            existing = Group.objects.filter(name=new).first()
            if existing and existing.pk != legacy.pk:
                for u in legacy.user_set.all():
                    u.groups.add(existing)
                for p in legacy.permissions.all():
                    existing.permissions.add(p)
                legacy.delete()
            else:
                legacy.name = new
                legacy.save(update_fields=['name'])
            renamed.append((old, new))

        if renamed:
            self.stdout.write(self.style.MIGRATE_HEADING('\nMigración de nombres:'))
            for old, new in renamed:
                self.stdout.write(self.style.WARNING(f"  {old}  →  {new}"))

    def _setup_groups(self, dry: bool) -> None:
        ct = ContentType.objects.get_for_model(PautaAssignmentModel)

        self.stdout.write(self.style.MIGRATE_HEADING('\nGrupos y permisos:'))
        for spec in WORK_GROUPS:
            codename, label = spec['permission']
            perm, p_created = Permission.objects.get_or_create(
                codename=codename, content_type=ct, defaults={'name': label},
            )
            if not p_created and perm.name != label:
                perm.name = label
                perm.save(update_fields=['name'])

            group, g_created = Group.objects.get_or_create(name=spec['name'])
            group.permissions.add(perm)

            self.stdout.write(self.style.SUCCESS(
                f"  {'+' if g_created else '='} {spec['name']:<22}  perm={codename}  home={spec['home']}"
            ))

    def _enroll_users(self, dry: bool) -> None:
        from apps.personnel.models.personnel import PersonnelProfile

        self.stdout.write(self.style.MIGRATE_HEADING('\nInscripción de usuarios por position_type:'))

        profiles = (
            PersonnelProfile.objects
            .filter(is_active=True, user__isnull=False, position_type__in=POSITION_TYPE_TO_GROUP.keys())
            .select_related('user')
        )

        by_group: dict[str, int] = {}
        skipped_no_user = 0

        for profile in profiles:
            user = profile.user
            if not user:
                skipped_no_user += 1
                continue

            group_name = POSITION_TYPE_TO_GROUP[profile.position_type]
            group = Group.objects.get(name=group_name)

            if not user.groups.filter(pk=group.pk).exists():
                user.groups.add(group)
                by_group[group_name] = by_group.get(group_name, 0) + 1
                self.stdout.write(
                    f"  + {user.username or user.email:<30}  ({profile.position_type})  → {group_name}"
                )

        if not by_group:
            self.stdout.write(self.style.WARNING('  (sin cambios — todos ya están inscritos)'))
        else:
            self.stdout.write('')
            for g, n in sorted(by_group.items()):
                self.stdout.write(self.style.SUCCESS(f"  {g:<22}  +{n} usuario(s)"))

        if skipped_no_user:
            self.stdout.write(self.style.WARNING(
                f"  ({skipped_no_user} perfil(es) sin usuario asociado — omitidos)"
            ))
