from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.core.management import CommandError


class Command(BaseCommand):
    """Enable/disable users from CSV string command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            'users',
            nargs='+',
            type=str
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            dest='disable',
            default=False,
            help='Disable the users',
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            dest='enable',
            default=False,
            help='Enable the users',
        )

    def handle(self, *args, **options):
        """Handle."""
        if not options['disable'] and not options['enable']:
            raise CommandError('Pass either --enable or --disable')
        if options['disable'] and options['enable']:
            raise CommandError('Pass either --enable or --disable not both')
        user_model = get_user_model()
        if options['enable']:
            enabled = True
        else:
            enabled = False
        user_model.objects.filter(email__in=options['users']).update(enabled=enabled)
