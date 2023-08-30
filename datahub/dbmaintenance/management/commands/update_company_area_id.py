from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models import Company


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to update address_area_id to None for companies with a given company address_country_id
    and area id match.
    """

    help = ('Updates address_area_id to None for companies with the specified '
            'address_country_id and area_id criteria.')

    def add_arguments(self, parser):
        parser.add_argument('area_id', type=str, help='UUID of the AdministrativeArea')
        parser.add_argument(
            'address_country_id',
            type=str,
            help='UUID of the Company’s address country',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        area_id = options['area_id']
        address_country_id = options['address_country_id']

        # Fetch companies based on criteria
        matching_companies = Company.objects.filter(
            address_area_id=area_id,
            address_country_id=address_country_id,
        )

        if matching_companies.exists():
            # Update the companies in a versioned way
            with reversion.create_revision():
                matching_companies.update(address_area_id=None)
                reversion.set_comment('Set address_area_id to None')

            # Output message
            self.stdout.write(self.style.SUCCESS(
                f'Updated {matching_companies.count()} companies, set address_area_id to None.',
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'No matching companies found. No updates were made.',
            ))
