import reversion

from datahub.company.models import Advisor
from datahub.dbmaintenance.management.base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update adviser.telephone_number."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        adviser = Advisor.objects.get(pk=row['id'])
        telephone_number = row['telephone_number']

        if adviser.telephone_number != telephone_number:
            adviser.telephone_number = telephone_number

            if not simulate:
                with reversion.create_revision():
                    adviser.save(update_fields=('telephone_number',))
                    reversion.set_comment('Telephone number migration.')
