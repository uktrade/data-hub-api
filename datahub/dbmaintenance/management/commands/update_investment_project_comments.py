import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.investment.models import InvestmentProject


class Command(CSVBaseCommand):
    """Command to update investment_project.description."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        # "Id" is not a typo
        investment_project = InvestmentProject.objects.get(pk=row['Id'])
        comments = row['comments'].strip()

        if investment_project.comments != comments:
            investment_project.comments = comments

            if not simulate:
                with reversion.create_revision():
                    investment_project.save(update_fields=('comments',))
                    reversion.set_comment('Comments migration.')
