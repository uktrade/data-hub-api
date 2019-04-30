from logging import getLogger
from types import SimpleNamespace

import reversion
from django.core.management.base import BaseCommand

from datahub.company.models import Company
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)


def copy_registered_address(destination_company, source_company):
    """
    Copy registered_address field values that are different from source
    Company to destination Company.
    :param destination_company: The registered_address fields for this
    object will be updated.
    :param source_company: The registered_address fields for this object will
    be copied to destination object.
    :returns copy_count: Number of fields that were copied
    """
    fields = {
        'registered_address_1',
        'registered_address_2',
        'registered_address_town',
        'registered_address_county',
        'registered_address_country',
        'registered_address_postcode',
    }

    copy_count = 0

    for field in fields:
        destination = getattr(destination_company, field)
        source = getattr(source_company, field)
        if destination != source:
            setattr(destination_company, field, source)
            copy_count += 1

    return copy_count > 0


class Command(BaseCommand):
    """
    Command to update registered_address for Company with
    the corresponding ComapiesHouseCompany registered_address.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulates the command by running the code without saving the changes',
        )

    @staticmethod
    def _get_companies_queryset():
        return Company.objects.all()

    @disable_search_signal_receivers(Company)
    def handle(self, *args, **options):
        """Handles the command."""
        logger.info('Started')

        result = {True: 0, False: 0}

        for company in self._get_companies_queryset().iterator():
            succeeded = self.process_company(
                company,
                simulate=options['simulate'],
            )
            result[succeeded] += 1

        logger.info(f'Finished - succeeded: {result[True]}, failed: {result[False]}')

    @staticmethod
    def _process_company(company, simulate=False):
        """
        Update the address of the Company to the
        address of the CompanyHouseCompany.
        """
        ch_company = company.companies_house_data

        if ch_company is None:
            # There is no corresponding CH record so we reset
            # the address by assigning empty values to fields
            ch_company = SimpleNamespace(**{
                'registered_address_1': '',
                'registered_address_2': '',
                'registered_address_town': '',
                'registered_address_county': '',
                'registered_address_country': None,
                'registered_address_postcode': '',
            })

        copied = copy_registered_address(company, ch_company)

        if not simulate and copied:
            with reversion.create_revision():
                company.save()
                reversion.set_comment('Updated registered address using CompaniesHouse data.')

    def process_company(self, company, simulate=False):
        """
        Wrapper around _process_company to catch potential problems.

        :param company: Company object
        :param simulate: if True, the changes will not be saved
        :returns: bool indicating if the company was processed successfully
        """
        try:
            self._process_company(company, simulate=simulate)
            logger.info(f'Company {company.name} - OK')
            return True
        except Exception as exc:
            logger.exception(f'Company {company.name} - {company.id} failed: {repr(exc)}')
            return False
