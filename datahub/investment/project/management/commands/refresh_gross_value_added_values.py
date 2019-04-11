from django.core.management.base import BaseCommand

from datahub.investment.project.tasks import (
    refresh_gross_value_added_value_for_fdi_investment_projects,
)


class Command(BaseCommand):
    """Command to refresh the Gross Value Added values for all fdi investment projects."""

    help = 'Refreshes all FDI investment projects that have or require a GVA to be set.'

    def handle(self, *args, **options):
        """
        Main method to loop over all investment projects that GVA
        could be calculated for and saving the project.

        Saving the project in turn calls the pre_save method
        'update_gross_value_added_for_investment_project_pre_save'
        which sets the Gross Value added data for a project.
        """
        refresh_gross_value_added_value_for_fdi_investment_projects()
