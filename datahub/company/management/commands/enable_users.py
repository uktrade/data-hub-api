from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    """Enable users from CSV string command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            'users',
            nargs='+',
            type='str'
        )

    def handle(self, *args, **options):
        """Handle."""
        user_model = get_user_model()
        user_model.objects.filter(email__in=options['users']).update(enabled=True)
