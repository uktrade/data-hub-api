from logging import getLogger

import reversion

from django.db import transaction
from django.utils.timezone import now
from tqdm import tqdm

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)

BATCH_SIZE = 2000


class Command(CSVBaseCommand):
    """Command to update Company.export_potential."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        score_dict = {value.lower(): key for key, value in Company.ExportPotentialScore.choices}
        company_number = parse_limited_string(row['company_number'])
        raw_potential = parse_limited_string(row['propensity_label'])

        try:
            export_potential = score_dict[raw_potential.lower()]
            return company_number, export_potential
        except KeyError:
            logger.warning(f'Invalid export potential for company number: {company_number}')
            return None

    @disable_search_signal_receivers(Company)
    def _handle(self, *args, **options):
        """Override to add batch processing and progress feedback."""
        rows = self._parse_csv(options['csv_file'])

        updates = []
        for row in tqdm(rows, desc='Processing companies'):
            result = self._process_row(row, **options)
            if result:
                company_number, export_potential = result
                try:
                    company = Company.objects.get(company_number=company_number)
                    if company.export_potential != export_potential:
                        company.export_potential = export_potential
                        company.last_modified_potential = now().date()
                        updates.append(company)

                        if len(updates) >= BATCH_SIZE:
                            self._update_batch(updates, options['simulate'])
                            updates = []
                except Company.DoesNotExist:
                    logger.warning(f'Company not found for company number: {company_number}')
                except Company.MultipleObjectsReturned:
                    logger.warning(f'Multiple companies found for: {company_number}')

        if updates:
            self._update_batch(updates, options['simulate'])

    def _update_batch(self, companies, simulate):
        """Updates a batch of companies."""
        if simulate:
            logger.info(f'Simulating update for {len(companies)} companies')
            return

        with transaction.atomic(), reversion.create_revision():
            Company.objects.bulk_update(companies, ['export_potential', 'last_modified_potential'])
            reversion.set_comment('Batch update of export potential and last modified date')
            logger.info(f'Updated {len(companies)} companies')
