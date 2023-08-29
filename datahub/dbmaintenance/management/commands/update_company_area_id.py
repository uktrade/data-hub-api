from logging import getLogger

import reversion

from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models import Company

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to update address_area_id to None for companies with a given company id
    and area id match.
    """

    help = ('Updates address_area_id to None for companies with the specified '
            'company_id and area_id criteria.')

    def add_arguments(self, parser):
        parser.add_argument('area_id', type=str, help='UUID of the AdministrativeArea')
        parser.add_argument('company_id', type=str, help='UUID of the Company')

    @transaction.atomic
    def handle(self, *args, **options):
        area_id = options['area_id']
        company_id = options['company_id']

        # Fetch companies based on criteria
        matching_companies = Company.objects.filter(
            address_area_id=area_id,
            id=company_id,
        )

        # Update the companies in a versioned way
        with reversion.create_revision():
            matching_companies.update(address_area_id=None)
            reversion.set_comment('Set address_area_id to None for the given company and area id')

        # Output message
        self.stdout.write(self.style.SUCCESS(
            f'Updated {matching_companies.count()} companies, set address_area_id to None.',
        ))
