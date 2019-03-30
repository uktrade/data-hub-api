from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.investment.project.models import InvestmentProject


class Command(BaseCommand):
    """Command to populate the Gross Value Added for all fdi investment projects."""

    help = 'Updates all FDI investment projects that require a GVA multiplier to be set.'

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
            project.save()

    def get_investment_projects(self):
        """Get investment projects. returns: All projects that GVA could be calculated for."""
        return InvestmentProject.objects.filter(
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            foreign_equity_investment__isnull=False,
        ).filter(
            Q(
                sector__isnull=False,
            ) | Q(
                business_activities=InvestmentBusinessActivityConstant.retail.value.id,
            ),
        )
