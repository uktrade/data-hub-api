import logging

from django.core.management.base import BaseCommand

from datahub.company_activity.models import GreatExportEnquiry


logger = logging.getLogger(__name__)


# TODO: Remove command once it has been run as one-off data modification


class Command(BaseCommand):
    """Command to do a one-off modification of GreatExportEnquiry submission type & action"""

    help = 'Swap values of submission_type & submission_action'

    def handle(self, *args, **options):
        """Swaps the values stored in the fields submission_type & submission_action"""
        great_list = GreatExportEnquiry.objects.all()

        for great in great_list:
            try:
                submission_type = great.submission_type
                submission_action = great.submission_action

                great.submission_action = submission_type
                great.submission_type = submission_action

            except Exception as e:
                logger.error(
                    f'An error occurred trying to modify GreatExportEnquiry id: {great.id}'
                    f' companny fields submission_action & submission_type: {str(e)}',
                )

        GreatExportEnquiry.objects.bulk_update(
            great_list,
            ['submission_action', 'submission_type'],
        )
