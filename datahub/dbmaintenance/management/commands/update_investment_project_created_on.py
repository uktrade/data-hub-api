import reversion
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import utc

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.investment.models import InvestmentProject


class Command(CSVBaseCommand):
    """Command to update investment_project.created_on."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])
        # there is no typo in 'createdon'
        created_on = dateutil_parse(row['createdon'])
        created_on = created_on.replace(tzinfo=created_on.tzinfo or utc)

        if investment_project.created_on != created_on:
            investment_project.created_on = created_on

            if not simulate:
                with reversion.create_revision():
                    investment_project.save(update_fields=('created_on',))
                    reversion.set_comment('Created On migration.')
