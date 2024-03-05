from logging import getLogger

import reversion

from django.db import transaction
from django.utils.timezone import now

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.export_potential."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        score_dict = {value.lower(): key for key, value in Company.ExportPotentialScore.choices}

        company_number = parse_limited_string(row['company_number'])
        raw_potential = parse_limited_string(row['propensity_label'])

        try:
            export_potential = score_dict[raw_potential.lower()]
        except KeyError:
            logger.warning(f'Invalid export potential: {raw_potential}')
            return

        try:
            company = Company.objects.get(company_number=company_number)
        except Company.DoesNotExist:
            logger.warning(f'Company not found for company number: {company_number}')
            return
        except Company.MultipleObjectsReturned:
            logger.error(f'Multiple companies found for company number: {company_number}')
            return

        if company.export_potential == export_potential:
            return

        company.export_potential = export_potential
        company.last_modified_potential = now().date()

        if not simulate:
            with transaction.atomic(), reversion.create_revision():
                company.save(update_fields=['export_potential', 'last_modified_potential'])
                reversion.set_comment('Export potential updated.')

    @disable_search_signal_receivers(Company)
    def _handle(self, *args, **options):
        """
        Disables search signal receivers for companies.
        Avoid queuing huge number of RQ scheduled tasks for syncing companies to OpenSearch.
        (Syncing can be manually performed afterwards using sync_search if required.)
        """
        return super()._handle(*args, **options)
