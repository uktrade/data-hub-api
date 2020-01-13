from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.dnb_api.constants import ALL_DNB_UPDATED_SERIALIZER_FIELDS
from datahub.dnb_api.tasks import get_company_updates

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to get the latest DNB company updates from dnb-service using the
    `datahub.dnb_api.tasks.get_company_updates` celery task.
    """

    help = (
        'Query dnb-service for the latest company updates and apply them to matching Data Hub '
        'company records.'
    )

    def add_arguments(self, parser):
        """
        Parse arguments/options for this command.
        """
        parser.add_argument(
            'last_updated_after',
            help=(
                'ISO format datetime string representing the datetime to query dnb-service with '
                'for latest updates.'
            ),
        )
        parser.add_argument(
            '-f',
            '--fields',
            nargs='+',
            help='The DNBCompanySerializer fields to update.',
            required=False,
            choices=ALL_DNB_UPDATED_SERIALIZER_FIELDS,
        )

    def handle(self, *args, **options):
        """
        Run the celery task.
        """
        get_company_updates.apply(
            kwargs={
                'last_updated_after': options['last_updated_after'],
                'fields_to_update': options['fields'],
            },
        )
