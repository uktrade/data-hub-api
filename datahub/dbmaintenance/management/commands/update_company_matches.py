import json
from base64 import b64decode

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.dnb_match.models import DnBMatchingResult


class Command(CSVBaseCommand):
    """Command to update DnBMatchingResult."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        company = Company.objects.get(pk=parse_uuid(row['id']))

        raw_data = b64decode(row['data'])
        data = json.loads(raw_data)

        if data and not simulate:
            DnBMatchingResult.objects.update_or_create(
                company_id=company.id,
                defaults={
                    'data': data,
                },
            )
