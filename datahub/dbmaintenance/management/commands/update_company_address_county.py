from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid, parse_limited_string, parse_uuid_list

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to set Company.address_county.
    """

    def _process_row(self, row, simulate=False, **options):
        """Processes a CSV file row."""
        pk = parse_uuid(row['UUID'])

        company = Company.objects.get(pk=pk)

        old_company_address_county = parse_uuid_list(row['old_company_address_county'])
        new_company_address_county = parse_uuid_list(row['new_company_address_county'])

        current_company_address_county = company.address_county.all()
        current_company_address_county_ids = {address_county.pk for address_county in current_company_address_county}

        if current_company_address_county_ids == set(new_company_address_county):
            return


        # not sure if this is needed
        if current_company_address_county_ids != set(old_company_address_county):
            logger.warning('Not updating company as its address county have changed', pk)
            return

        if simulate:
            return

        # new_company_address_county = parse_limited_string(row['company_address_county'])
        #
        # company.address_county = new_company_address_county

        with reversion.create_revision():
            company.save(update_fields=('address_county',))
            reversion.set_comment('Company county address updated.')
