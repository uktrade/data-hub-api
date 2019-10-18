from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_bool, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.great_profile_status."""

    def _process_row(self, row, simulate=False, **options):
        """
        Process one single row.
        """
        pk = parse_uuid(row['datahub_company_id'])
        company = Company.objects.get(pk=pk)
        has_profile = parse_bool(row['has_find_a_supplier_profile'])
        is_published = parse_bool(row['is_published_find_a_supplier'])

        profile_status = None
        if has_profile and is_published:
            profile_status = Company.GREAT_PROFILE_STATUSES.published
        elif has_profile:
            profile_status = Company.GREAT_PROFILE_STATUSES.unpublished

        if company.great_profile_status == profile_status:
            return

        company.great_profile_status = profile_status

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('great_profile_status',))
            reversion.set_comment('GREAT profile status updated.')
