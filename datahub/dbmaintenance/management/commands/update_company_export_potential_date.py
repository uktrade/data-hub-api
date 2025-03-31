import codecs
import csv
from contextlib import closing
from logging import getLogger

import reversion
from django.db import transaction
from django.utils.timezone import now

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string
from datahub.documents.utils import get_s3_client_for_bucket
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
        """Internal version of the `handle` method, adapted for streaming and batching from S3.

        :returns: dict with count of records successful and failed updates
        """
        result = {True: 0, False: 0}
        batch_size = options.get('batch_size', 5000)

        s3_client = get_s3_client_for_bucket('default')
        response = s3_client.get_object(
            Bucket=options['bucket'],
            Key=options['object_key'],
        )['Body']

        with closing(response):
            csvfile = codecs.getreader('utf-8')(response)
            reader = csv.DictReader(csvfile)
            batch = []

            for row in reader:
                batch.append(row)
                if len(batch) >= batch_size:
                    for row in batch:  # noqa: PLW2901
                        succeeded = self.process_row(row, **options)
                        result[succeeded] += 1
                    batch = []

            if batch:
                for row in batch:
                    succeeded = self.process_row(row, **options)
                    result[succeeded] += 1

        return result
