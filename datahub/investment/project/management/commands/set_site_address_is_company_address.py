import logging

from django.core.management.base import BaseCommand

from datahub.investment.project.models import InvestmentProject


logger = logging.getLogger(__name__)


# TODO: Remove command once it has been run as one-off data modification


class Command(BaseCommand):
    """Command to do a one-off modification of investment projects."""

    help = 'Sets site_address_is_company_address value for existing projects.'

    def handle(self, *args, **options):
        """Method to set site_address_is_company_address value for existing projects.

        Business rules are as follows for projects that have:
        - site_address_is_company_address == None and site_decided == True: set
        site_address_is_company_address to False.
        - site_address_is_company_address == None and site_decided == False/None: leave
        site_address_is_company_address as None.
        """
        try:
            projects = InvestmentProject.objects.filter(
                site_address_is_company_address__isnull=True,
                site_decided=True,
            )
            if projects.exists():
                logger.info(
                    f'Found {projects.count()} projects with '
                    'site_address_is_company_address == None and site_decided == True. '
                    'Modifying...',
                )
                updated_count = projects.update(site_address_is_company_address=False)
                logger.info(
                    f'Set site_address_is_company_address to False on {updated_count} projects.',
                )
            else:
                logger.warning(
                    'No projects with '
                    'site_address_is_company_address == None and site_decided == True found. '
                    'Exiting...',
                )
        except Exception as e:
            logger.error(
                'An error occurred trying to set site_address_is_company_address '
                f'value for existing projects: {str(e)}',
            )
