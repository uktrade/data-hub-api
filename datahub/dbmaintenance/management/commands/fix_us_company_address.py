from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.core.constants import Country
from datahub.core.postcode_constants import CountryPostcodeReplacement, US_ZIP_STATES
from datahub.dbmaintenance.resolvers.company_address import (
    CompanyAddressResolver,
)

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to make US postcodes conform to a standard format and update states
    accordingly.
    Example of executing this command locally:
        python manage.py fix_us_company_address
        or use the makefile for developers
    """

    help = 'Fix US Company address postcodes for the purpose of setting address areas'

    def handle(self, *args, **options):
        """
        Resolves Company address issues for the United States
        """
        company_address_resolver = CompanyAddressResolver(
            country_id=Country.united_states.value.id,
            revision_comment='US Area and postcode Fix.',
            zip_states=US_ZIP_STATES,
            postcode_replacement=CountryPostcodeReplacement.united_states.value,
        )
        company_address_resolver.run()
