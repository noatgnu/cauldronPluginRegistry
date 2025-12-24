from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decouple import config

class Command(BaseCommand):
    help = 'Creates a superuser if one does not exist.'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser already exists.'))
            return

        username = config('ADMIN_USER', default=None)
        email = config('ADMIN_EMAIL', default=None)
        password = config('ADMIN_PASSWORD', default=None)

        if not all([username, email, password]):
            self.stdout.write(self.style.WARNING(
                'ADMIN_USER, ADMIN_EMAIL, and ADMIN_PASSWORD environment variables are not set. '
                'Skipping superuser creation.'
            ))
            return

        self.stdout.write(f'Creating superuser: {username}')
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS('Superuser created successfully.'))
