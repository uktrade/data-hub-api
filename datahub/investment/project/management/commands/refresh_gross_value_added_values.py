from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.investment.project.models import InvestmentProject


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
        investment_projects = self.get_investment_projects()
        for project in investment_projects.iterator():
            project.save(update_fields=['gross_value_added', 'gva_multiplier'])

    def get_investment_projects(self):
        """Get investment projects. returns: All projects that GVA can be calculated for."""
        return InvestmentProject.objects.filter(
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            foreign_equity_investment__isnull=False,
        ).filter(
            Q(
                sector__isnull=False,
            ) | Q(
                business_activities__in=[
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.sales.value.id,
                ],
            ),
        )
