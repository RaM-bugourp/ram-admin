"""Management command — create default superuser."""
from django.core.management.base import BaseCommand
from apps.rbac.models import User


class Command(BaseCommand):
    help = 'Initialize RBAC data and create a superuser'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@adminx.local'
        password = 'admin123'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists, skipping.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created.'))
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
