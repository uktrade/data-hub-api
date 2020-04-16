from secrets import token_urlsafe

from django.core.management import BaseCommand, CommandError

from datahub.company.models import Advisor
from datahub.oauth.cache import add_token_data_to_cache


class Command(BaseCommand):
    """Temporarily adds an access token for local development purposes."""

    help = """Temporarily adds an access token for local development purposes."""
    requires_migrations_checks = True

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            'sso_email_user_id',
            help='The SSO email user ID of the adviser to add an access token for.',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=10,
            help='Number of hours in which the access token will expire.',
        )
        parser.add_argument(
            '--token',
            type=str,
            help='If specified, a token will not be randomly generated and the specified value '
                 'will be used instead.',
        )

    def handle(self, *args, **options):
        """Main logic for the actual command."""
        sso_email_user_id = options['sso_email_user_id']
        token = options['token'] or token_urlsafe()
        hours = options['hours']
        timeout = hours * 60 * 60

        try:
            adviser = Advisor.objects.get(sso_email_user_id=sso_email_user_id)
        except Advisor.DoesNotExist:
            raise CommandError(f'No adviser with SSO email user ID {sso_email_user_id} found.')

        add_token_data_to_cache(token, adviser.email, adviser.sso_email_user_id, timeout)

        msg = f'The token {token} was successfully added and will expire in {hours} hours.'
        return self.style.SUCCESS(msg)
