from django.core.management.base import BaseCommand
from cryptography.fernet import Fernet


class Command(BaseCommand):
    help = 'Generate a Fernet encryption key for encrypting SSH keys and passphrases'

    def handle(self, *args, **options):
        key = Fernet.generate_key().decode()

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('Generated Encryption Key:'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'\n{key}\n')

        self.stdout.write(self.style.WARNING('\n' + '=' * 70))
        self.stdout.write(self.style.WARNING('Setup Instructions:'))
        self.stdout.write(self.style.WARNING('=' * 70))

        self.stdout.write('\n1. Add to your Django settings.py:')
        self.stdout.write(f"   ENCRYPTION_KEY = '{key}'")

        self.stdout.write('\n2. Or set as environment variable (recommended):')
        self.stdout.write(f"   export ENCRYPTION_KEY='{key}'")

        self.stdout.write('\n   Then in settings.py:')
        self.stdout.write('   import os')
        self.stdout.write("   ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')")

        self.stdout.write(self.style.ERROR('\n' + '=' * 70))
        self.stdout.write(self.style.ERROR('IMPORTANT SECURITY NOTES:'))
        self.stdout.write(self.style.ERROR('=' * 70))
        self.stdout.write('\n- NEVER commit this key to version control')
        self.stdout.write('- Back up this key securely (password manager, encrypted file)')
        self.stdout.write('- If you lose this key, all encrypted SSH keys will be unrecoverable')
        self.stdout.write('- Store in environment variables for production')
        self.stdout.write('\n')
