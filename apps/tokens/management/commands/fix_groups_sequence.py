"""
Fix groups sequence and assign token permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import connection
from django.db.models import Max


class Command(BaseCommand):
    help = 'Fix groups sequence and assign token permissions'

    def handle(self, *args, **options):
        # Fix the sequence first
        self.stdout.write('Fixing auth_group sequence...')

        max_id = Group.objects.aggregate(max_id=Max('id'))['max_id'] or 0
        self.stdout.write(f'Max group ID: {max_id}')

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('auth_group', 'id'), %s, true)",
                [max_id]
            )

        self.stdout.write(self.style.SUCCESS('Sequence fixed!'))

        # Now add token permissions to MANAGING group
        self.stdout.write('\nAdding token permissions to MANAGING group...')

        try:
            managing_group = Group.objects.get(name='MANAGING')
        except Group.DoesNotExist:
            managing_group = Group.objects.create(name='MANAGING')
            self.stdout.write(self.style.WARNING('Created MANAGING group'))

        token_permissions = ['view_tokenrequest', 'add_tokenrequest', 'change_tokenrequest']

        for codename in token_permissions:
            try:
                perm = Permission.objects.get(
                    codename=codename,
                    content_type__app_label='tokens'
                )
                managing_group.permissions.add(perm)
                self.stdout.write(f'  Added: tokens.{codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Not found: tokens.{codename}'))

        self.stdout.write(self.style.SUCCESS('\nDone!'))

        # List current MANAGING permissions
        self.stdout.write('\nMANAGING group permissions:')
        for perm in managing_group.permissions.all():
            self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename}')
