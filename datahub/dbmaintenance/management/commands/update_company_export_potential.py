from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.export_potential."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        score_dict = {value.lower(): key for key, value in Company.EXPORT_POTENTIAL_SCORES}

        pk = parse_uuid(row['datahub_company_id'])
        company = Company.objects.get(pk=pk)
        raw_potential = parse_limited_string(row['export_propensity'])
        export_potential = score_dict[raw_potential.lower()]

        if company.export_potential == export_potential:
            return

        company.export_potential = export_potential

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('export_potential',))
            reversion.set_comment('Export potential updated.')
