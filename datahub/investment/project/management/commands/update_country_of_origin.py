from django.core.management.base import BaseCommand

from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.tasks import (
    schedule_update_country_of_origin_for_investment_projects,
)
from datahub.search.signals import disable_search_signal_receivers


class Command(BaseCommand):
    """
    Command to update the country of origin values for investment projects.

    Search signal receivers for InvestmentProject are being disabled to avoid queueing huge
    amount of RQ tasks to refresh the object in OpenSearch.

    OpenSearch should be manually synchronised after running the command.
    """

    help = 'Updates all investment projects that do not have country of origin set.'

    @disable_search_signal_receivers(InvestmentProject)
    def handle(self, *args, **options):
        """
        Schedule main method to loop over all investment projects that do not have country of
        origin set.
        """
        schedule_update_country_of_origin_for_investment_projects()
