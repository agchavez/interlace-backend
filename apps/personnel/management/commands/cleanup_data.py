"""
Management command to clean up data for a fresh start.
Deletes: tokens, notifications, certifications, medical records,
emergency contacts, personnel profiles, push subscriptions,
and users (except protected emails).

Usage:
    # Dry run (validation only - default)
    python manage.py cleanup_data

    # Execute deletion
    python manage.py cleanup_data --confirm
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.user.models.user import UserModel
from apps.user.models.notificacion import NotificationModel
from apps.user.models.push_subscription import PushSubscription
from apps.tokens.models.base import TokenRequest
from apps.tokens.models.exit_pass import ExitPassDetail, ExitPassItem
from apps.tokens.models.external_person import ExternalPerson
from apps.personnel.models.personnel import PersonnelProfile, EmergencyContact
from apps.personnel.models.certification import Certification, CertificationType
from apps.personnel.models.medical import MedicalRecord

PROTECTED_EMAILS = [
    'ricardo.salinas@ab-inbev.com',
    'achavez@unah.hn',
    'agchavez@unah.hn',
]


class Command(BaseCommand):
    help = 'Clean up data for fresh start. Use --confirm to execute.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually execute the deletion. Without this flag, only shows what would be deleted.',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        mode = 'EJECUCION' if confirm else 'VALIDACION (dry-run)'
        self.stdout.write(self.style.WARNING(f'\n{"="*60}'))
        self.stdout.write(self.style.WARNING(f'  MODO: {mode}'))
        self.stdout.write(self.style.WARNING(f'{"="*60}\n'))

        # --- Users to protect ---
        protected_users = UserModel.objects.filter(email__in=PROTECTED_EMAILS)
        protected_ids = list(protected_users.values_list('id', flat=True))

        self.stdout.write(self.style.SUCCESS('Usuarios PROTEGIDOS (NO se eliminaran):'))
        for u in protected_users:
            self.stdout.write(f'  - {u.email} (id={u.id}, {u.first_name} {u.last_name})')

        if len(protected_ids) != len(PROTECTED_EMAILS):
            found_emails = set(protected_users.values_list('email', flat=True))
            missing = set(PROTECTED_EMAILS) - found_emails
            self.stdout.write(self.style.ERROR(
                f'\n  ADVERTENCIA: Estos emails protegidos NO existen en la BD: {missing}'
            ))

        # --- Users to delete ---
        users_to_delete = UserModel.objects.exclude(id__in=protected_ids)
        self.stdout.write(f'\nUsuarios a ELIMINAR: {users_to_delete.count()}')
        for u in users_to_delete:
            self.stdout.write(f'  - {u.email} (id={u.id}, {u.first_name} {u.last_name})')

        # --- Tokens ---
        # Token details (exit pass items, exit pass details, and other detail models)
        exit_pass_items = ExitPassItem.objects.all()
        exit_pass_details = ExitPassDetail.objects.all()
        tokens = TokenRequest.objects.all()
        external_persons = ExternalPerson.objects.all()

        self.stdout.write(f'\nTokens (ExitPassItems): {exit_pass_items.count()}')
        self.stdout.write(f'Tokens (ExitPassDetails): {exit_pass_details.count()}')
        self.stdout.write(f'Tokens (TokenRequest): {tokens.count()}')
        self.stdout.write(f'Personas externas: {external_persons.count()}')

        # --- Token detail models (permit hours, days, etc.) ---
        token_detail_counts = self._count_token_details()

        # --- Notifications ---
        notifications = NotificationModel.objects.all()
        self.stdout.write(f'\nNotificaciones: {notifications.count()}')

        # --- Push subscriptions ---
        push_subs = PushSubscription.objects.all()
        self.stdout.write(f'Push Subscriptions: {push_subs.count()}')

        # --- Certifications ---
        certifications = Certification.objects.all()
        self.stdout.write(f'\nCertificaciones: {certifications.count()}')

        # --- Medical records ---
        medical_records = MedicalRecord.objects.all()
        self.stdout.write(f'Registros medicos: {medical_records.count()}')

        # --- Emergency contacts ---
        emergency_contacts = EmergencyContact.objects.all()
        self.stdout.write(f'Contactos de emergencia: {emergency_contacts.count()}')

        # --- Personnel profiles ---
        # Protect profiles linked to protected users
        personnel_profiles = PersonnelProfile.objects.exclude(user_id__in=protected_ids)
        protected_profiles = PersonnelProfile.objects.filter(user_id__in=protected_ids)
        self.stdout.write(f'\nPerfiles de personal a ELIMINAR: {personnel_profiles.count()}')
        self.stdout.write(f'Perfiles de personal PROTEGIDOS: {protected_profiles.count()}')
        for p in protected_profiles:
            self.stdout.write(f'  - {p.first_name} {p.last_name} (code={p.employee_code})')

        # --- Summary ---
        self.stdout.write(self.style.WARNING(f'\n{"="*60}'))
        self.stdout.write(self.style.WARNING('  RESUMEN DE ELIMINACION'))
        self.stdout.write(self.style.WARNING(f'{"="*60}'))

        total = 0
        items = [
            ('Exit Pass Items', exit_pass_items.count()),
            ('Exit Pass Details', exit_pass_details.count()),
            ('Token Requests', tokens.count()),
            ('Personas Externas', external_persons.count()),
            ('Notificaciones', notifications.count()),
            ('Push Subscriptions', push_subs.count()),
            ('Certificaciones', certifications.count()),
            ('Registros Medicos', medical_records.count()),
            ('Contactos de Emergencia', emergency_contacts.count()),
            ('Perfiles de Personal', personnel_profiles.count()),
            ('Usuarios', users_to_delete.count()),
        ]
        # Add token detail counts
        items = token_detail_counts + items

        for name, count in items:
            total += count
            self.stdout.write(f'  {name}: {count}')

        self.stdout.write(self.style.WARNING(f'\n  TOTAL registros a eliminar: {total}'))
        self.stdout.write(self.style.WARNING(f'{"="*60}\n'))

        if not confirm:
            self.stdout.write(self.style.NOTICE(
                'Este fue un DRY RUN. Para ejecutar la eliminacion, corra:\n'
                '  python manage.py cleanup_data --confirm\n'
            ))
            return

        # --- EXECUTE DELETION ---
        self.stdout.write(self.style.ERROR('Ejecutando eliminacion...'))

        with transaction.atomic():
            # 1. Token detail children first (exit pass items)
            c = exit_pass_items.delete()[0]
            self.stdout.write(f'  Eliminados ExitPassItems: {c}')

            c = exit_pass_details.delete()[0]
            self.stdout.write(f'  Eliminados ExitPassDetails: {c}')

            # Delete other token detail models
            self._delete_token_details()

            # 2. Token requests (CASCADE will clean remaining details)
            c = tokens.delete()[0]
            self.stdout.write(f'  Eliminados TokenRequests: {c}')

            c = external_persons.delete()[0]
            self.stdout.write(f'  Eliminados ExternalPerson: {c}')

            # 3. Notifications
            c = notifications.delete()[0]
            self.stdout.write(f'  Eliminadas Notificaciones: {c}')

            # 4. Push subscriptions
            c = push_subs.delete()[0]
            self.stdout.write(f'  Eliminados Push Subscriptions: {c}')

            # 5. Certifications (all, including from protected profiles)
            c = certifications.delete()[0]
            self.stdout.write(f'  Eliminadas Certificaciones: {c}')

            # 6. Medical records
            c = medical_records.delete()[0]
            self.stdout.write(f'  Eliminados Registros Medicos: {c}')

            # 7. Emergency contacts
            c = emergency_contacts.delete()[0]
            self.stdout.write(f'  Eliminados Contactos de Emergencia: {c}')

            # 8. Personnel profiles (except protected users')
            # First clear FK references from tokens to personnel about to be deleted
            c = personnel_profiles.delete()[0]
            self.stdout.write(f'  Eliminados Perfiles de Personal: {c}')

            # 9. Users (except protected)
            c = users_to_delete.delete()[0]
            self.stdout.write(f'  Eliminados Usuarios: {c}')

        self.stdout.write(self.style.SUCCESS('\nLimpieza completada exitosamente!'))

    def _count_token_details(self):
        """Count all token detail model instances."""
        counts = []
        try:
            from apps.tokens.models.permit_hour import PermitHourDetail
            counts.append(('Permit Hour Details', PermitHourDetail.objects.count()))
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.permit_day import PermitDayDetail, PermitDayDate
            counts.append(('Permit Day Dates', PermitDayDate.objects.count()))
            counts.append(('Permit Day Details', PermitDayDetail.objects.count()))
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.uniform_delivery import UniformDeliveryDetail, UniformItem
            counts.append(('Uniform Items', UniformItem.objects.count()))
            counts.append(('Uniform Delivery Details', UniformDeliveryDetail.objects.count()))
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.substitution import SubstitutionDetail
            counts.append(('Substitution Details', SubstitutionDetail.objects.count()))
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.rate_change import RateChangeDetail
            counts.append(('Rate Change Details', RateChangeDetail.objects.count()))
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.overtime import OvertimeDetail
            counts.append(('Overtime Details', OvertimeDetail.objects.count()))
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.shift_change import ShiftChangeDetail
            counts.append(('Shift Change Details', ShiftChangeDetail.objects.count()))
        except (ImportError, Exception):
            pass
        return counts

    def _delete_token_details(self):
        """Delete all token detail model instances."""
        try:
            from apps.tokens.models.permit_hour import PermitHourDetail
            c = PermitHourDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados PermitHourDetail: {c}')
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.permit_day import PermitDayDetail, PermitDayDate
            c = PermitDayDate.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados PermitDayDate: {c}')
            c = PermitDayDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados PermitDayDetail: {c}')
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.uniform_delivery import UniformDeliveryDetail, UniformItem
            c = UniformItem.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados UniformItem: {c}')
            c = UniformDeliveryDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados UniformDeliveryDetail: {c}')
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.substitution import SubstitutionDetail
            c = SubstitutionDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados SubstitutionDetail: {c}')
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.rate_change import RateChangeDetail
            c = RateChangeDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados RateChangeDetail: {c}')
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.overtime import OvertimeDetail
            c = OvertimeDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados OvertimeDetail: {c}')
        except (ImportError, Exception):
            pass
        try:
            from apps.tokens.models.shift_change import ShiftChangeDetail
            c = ShiftChangeDetail.objects.all().delete()[0]
            self.stdout.write(f'  Eliminados ShiftChangeDetail: {c}')
        except (ImportError, Exception):
            pass
