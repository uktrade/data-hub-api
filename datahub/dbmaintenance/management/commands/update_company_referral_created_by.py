from logging import getLogger

import reversion

from datahub.company_referral.models import CompanyReferral
from datahub.company.models import Advisor
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to set Company.created_on where missing.

    Some Company records have missing created_on values which
    besides being inconsistent with the parent BaseModel
    class is also causing these Companies to be omitted
    from Data Workspace.
    """

    def _process_row(self, row, simulate=False, **options):
        """Process a single row."""
        # .parse() creates a datetime object even in the absence of hours, minutes
        advisor_uuid = parse(row['Sender Advidor UUID'])

        pk = parse_uuid(row['UUID'])
        company_referral = CompanyReferral.objects.get(pk=pk)

        if simulate:
            return

        company_referral_sender_advisor = Advisor.objects.get(
            id=advisor_uuid,
        )

        company_referral.created_by = company_referral_sender_advisor
        
        with reversion.create_revision():
            company_referral.save(update_fields=('created_by',))
            reversion.set_comment('Sender Advisor updated.')
