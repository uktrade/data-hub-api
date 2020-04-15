from logging import getLogger

from django.core.management import BaseCommand

from datahub.company.models import Advisor
from datahub.oauth.sso_api_client import get_user_by_email, SSORequestError, SSOUserDoesNotExist
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to fill in black Advisor.sso_email_user_id by querying Staff SSO.

    This is a temporary command and will be removed once no longer required.

    TODO: Remove this command once it has been run in production and
    the new introspection logic is live.
    """

    help = """Populates adviser SSO email user IDs by querying Staff SSO."""
    requires_migrations_checks = True

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulate the command by querying Staff SSO but not saving changes.',
        )

    @disable_search_signal_receivers(Advisor)
    def handle(self, *args, **options):
        """Main logic for the actual command."""
        is_simulation = options['simulate']
        num_skipped = 0
        num_errored = 0
        num_updated = 0

        queryset = Advisor.objects.filter(is_active=True, sso_email_user_id__isnull=True)
        for adviser in queryset.iterator():
            try:
                sso_user_data = get_user_by_email(adviser.email)
            except SSOUserDoesNotExist:
                logger.warning(f'No SSO user found for adviser ID {adviser.pk}')
                num_skipped += 1
                continue
            except SSORequestError as exc:
                logger.warning(f'SSO request error {exc} for adviser ID {adviser.pk}')
                num_errored += 1
                continue

            # Only do the update if the primary emails match (otherwise this is a
            # duplicate or redundant adviser record)
            if adviser.email.lower() != sso_user_data['email'].lower():
                logger.warning(f'SSO primary email didn’t match for adviser ID {adviser.pk}')
                num_skipped += 1
                continue

            adviser.sso_email_user_id = sso_user_data['email_user_id']
            if not is_simulation:
                adviser.save(update_fields=('sso_email_user_id',))

            logger.info(f'SSO email user ID updated for adviser ID {adviser.pk}')
            num_updated += 1

        logger.info(f'{num_updated} advisers updated')
        logger.info(f'{num_skipped} advisers skipped')
        logger.info(f'{num_errored} advisers with errors')
