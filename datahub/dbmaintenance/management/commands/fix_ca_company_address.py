from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.core.constants import Country
from datahub.core.postcode_constants import CA_ZIP_STATES, CountryPostcodeReplacement
from datahub.dbmaintenance.resolvers.company_address \
    import CompanyAddressResolver

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to make CA postcodes conform to a standard format and update states
    accordingly.
    Example of executing this command locally:
        python manage.py fix_ca_company_address
        or use the makefile for developers
    """

    help = 'Fix Canadian Company address postcodes for the purpose of setting address areas'

    def handle(self, *args, **options):
        """
        Resolves Company address issues for Canada
        """
        company_address_resolver = CompanyAddressResolver(
            Country.canada.value.id,
            'Canada area and postcode fix.',
            CA_ZIP_STATES,
            CountryPostcodeReplacement.canada.value,
        )
        company_address_resolver.run()

    def add_arguments(self, parser):
        """
        No arguments needed for the management command.
        """
        pass
