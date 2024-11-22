import logging

from django.core.management.base import BaseCommand

from datahub.investment.project.constants import SpecificProgramme as SpecificProgrammeConstants
from datahub.investment.project.models import (
    InvestmentProject,
    SpecificProgramme,
)


REFERRED_TO_EYB_PROGRAMME_ID = SpecificProgrammeConstants.referred_to_eyb.value.id
REFERRED_STATUS_VALUE = InvestmentProject.Status.REFERRED.value
ONGOING_STATUS_VALUE = InvestmentProject.Status.ONGOING.value


logger = logging.getLogger(__name__)


# TODO: Remove command once it has been run as one-off data modification


class Command(BaseCommand):
    """Command to do a one-off modification of referred investment projects."""

    help = 'Modifies referred investment projects according to business rules.'

    def handle(self, *args, **options):
        """Method to iterate over `referred` projects and modify them.

        Modifications include:
        - Add the new `Referred to EYB` specific programme to their list of specific programmes
        - Set their status as `Ongoing`
        """
        try:
            referred_projects = InvestmentProject.objects.filter(
                status=REFERRED_STATUS_VALUE,
            )
            referred_to_eyb_programme = SpecificProgramme.objects.get(
                pk=REFERRED_TO_EYB_PROGRAMME_ID,
            )
            if referred_projects.exists():
                logger.info(f'Found {referred_projects.count()} referred projects. Modifying...')
                # many-to-many field needs to be updated individually
                for project in referred_projects:
                    project.specific_programmes.add(referred_to_eyb_programme)
                # bulk update status field
                referred_projects.update(status=ONGOING_STATUS_VALUE)
                logger.info('Finished modifying referred projects.')
            else:
                logger.warning('No referred projects found. Exiting...')
        except Exception as e:
            logger.error(f'An error occurred trying to modify referred projects: {str(e)}')
