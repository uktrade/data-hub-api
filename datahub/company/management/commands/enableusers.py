from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


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

    def handle(self, *args, **options):
        """Handle."""
        user_model = get_user_model()
        if options['disable']:
            enabled = False
        else:
            enabled = True
        user_model.objects.filter(email__in=options['users']).update(enabled=enabled)
