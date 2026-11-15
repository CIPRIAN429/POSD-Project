from django.core.management import BaseCommand, call_command, CommandError
from django.conf import settings
from pathlib import Path
import shutil


class Command(BaseCommand):
    help = 'Explicitly remove all application data and restore the synthetic demo.'

    def add_arguments(self, parser):
        parser.add_argument('--confirm-reset', action='store_true')

    def handle(self, *args, **options):
        if not options['confirm_reset']:
            raise CommandError('Use scripts/reset-demo.sh to confirm this operation.')
        call_command('flush', interactive=False)
        root = Path(settings.MEDIA_ROOT).resolve()
        # Clear only the configured private fixture folder, never the mount root.
        private = (root / 'private').resolve()
        if private.parent != root:
            raise CommandError('Invalid private storage path.')
        if private.exists():
            shutil.rmtree(private)
        call_command('seed_demo')
        self.stdout.write(self.style.SUCCESS('Demo restored.'))
