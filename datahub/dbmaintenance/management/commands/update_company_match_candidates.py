import json
from base64 import b64decode
from functools import lru_cache
from logging import getLogger

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.dnb_match.constants import DNB_COUNTRY_CODE_MAPPING
from datahub.dnb_match.models import DnBMatchingCSVRecord
from datahub.metadata.models import Country

logger = getLogger(__name__)

DNB_COUNTRY_MAPPING = {
    entry['name']: entry['iso_alpha2_code']
    for entry in DNB_COUNTRY_CODE_MAPPING.values()
}


class Command(CSVBaseCommand):
    """Command to update DnBMatchingCSVRecord."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--batch_number',
            type=int,
            help='Batch number - version of the match candidates.',
        )

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        company = Company.objects.get(pk=parse_uuid(row['id']))
        batch_number = options['batch_number']

        raw_data = b64decode(row['data'])
        data = json.loads(raw_data)

        if not self._validate_data(data):
            logger.warning(
                'Required fields are missing for given company: %s, %s',
                company.pk,
                data,
            )
            return

        enriched_data = self._resolve_dnb_address_country(data)
        if not enriched_data:
            logger.warning(
                'Could not resolve country for given company: %s, %s',
                company.pk,
                data,
            )
            return

        if not simulate:
            DnBMatchingCSVRecord.objects.update_or_create(
                company_id=company.id,
                defaults={
                    'batch_number': batch_number,
                    'data': enriched_data,
                },
            )

    def _validate_data(self, data):
        return all(row.keys() == DnBMatchingCSVRecord.EXPECTED_DATA_FIELDS for row in data)

    def _resolve_dnb_address_country(self, data):
        """Resolve DnB address_country with Data Hub country."""
        for row in data:
            country_code = DNB_COUNTRY_MAPPING.get(row['address_country'])
            country = self._get_dh_country_by_country_code(country_code) if country_code else None
            if not country:
                return None

            row['address_country'] = {
                'id': country.id,
                'name': country.name,
            }
        return data

    @lru_cache(maxsize=None)
    def _get_dh_country_by_country_code(self, country_code):
        return Country.objects.get(
            iso_alpha2_code=country_code,
        )
