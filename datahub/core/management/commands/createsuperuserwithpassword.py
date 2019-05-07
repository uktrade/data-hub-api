from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    """
    Create a superuser with a password.
    """

    help = (
        'Create a superuser with a password - the standard createsuperuser command '
        'is interactive, so password cannot be supplied on the CLI'
    )

    def add_arguments(self, parser):
        """
        Adds additional command arguments.
        """
        parser.add_argument(
            'username',
            type=str,
            help='The superuser\'s username',
        )
        parser.add_argument(
            'password',
            type=str,
            help='The superuser\'s password',
        )

    def handle(self, *args, **options):
        """
        Handle invocation of the command.
        """
        username = options['username']
        password = options['password']
        user = User.objects.create_superuser(username, password)
        self.stdout.write(self.style.SUCCESS(f'Successfully created user "{user.id}"'))
