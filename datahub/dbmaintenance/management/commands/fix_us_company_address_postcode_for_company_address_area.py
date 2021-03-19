from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from django.db.models import F, Func, Value

from datahub.company.models import Company
from datahub.core.constants import Country, US_ZIP_STATES
from datahub.metadata.models import AdministrativeArea

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to query for the ids of duns-linked companies for a particular set of
    one list tiers and (optionally) particular set of account managers.
    Example of executing this command locally:
        python manage.py fix_us_company_address_postcode_data
    """

    def add_arguments(self, parser):
        """
        No arguments needed for the management command.
        """
        pass

    def handle(self, *args, **options):
        """
        Run the query and output the results as an info message to the log file.
        """
        self.fix_postcodes_and_address_areas()

    def fix_postcodes_and_address_areas(self):
        """
        Does update on the postcode address table
        """
        with reversion.create_revision():
            self.update_address_postcode()
            self.update_registered_address_postcode()
            reversion.set_comment('Address Postcode Fix.')

        with reversion.create_revision():
            self.update_address_area()
            reversion.set_comment('Company Address Area Migration')

        with reversion.create_revision():
            self.update_registered_address_area()
            reversion.set_comment('Company Registered Address Area Migration')

    def update_registered_address_area(self):
        """
        Update company registered address area data
        """
        united_states_companies = Company.objects.filter(
            registered_address_country=Country.united_states.value.id,
        )

        for zip_prefix, area_code, _area_name in US_ZIP_STATES:
            administrative_area = self.us_administrative_area_by_code(area_code)

            self.companies_by_registered_address_postcode(
                united_states_companies,
                zip_prefix,
            ).update(registered_address_area_id=administrative_area.id)

    def update_address_area(self):
        """
        Update company address area data
        """
        united_states_companies = Company.objects.filter(
            address_country=Country.united_states.value.id,
        )

        for zip_prefix, area_code, _area_name in US_ZIP_STATES:
            administrative_area = self.us_administrative_area_by_code(area_code)
            self.companies_by_address_postcode(
                united_states_companies,
                zip_prefix,
            ).update(address_area_id=administrative_area.id)

    def companies_by_registered_address_postcode(self, united_states_companies, zip_prefix):
        """
        Filters United States Countries by registered address postcode equal to zip-prefix
        where no registered address area exists
        @param united_states_companies: united states company query
        @param zip_prefix: 3 digit zip prefix
        @return: Filtered Company by zip prefix and no registered address area
        """
        return united_states_companies.filter(
            registered_address_postcode__startswith=zip_prefix,
            registered_address_area_id__isnull=True,
        )

    def companies_by_address_postcode(self, united_states_companies, zip_prefix):
        """
        Filters United States Countries by address postcode equal to zip-prefix
        where no address area exists
        @param united_states_companies: united states company query
        @param zip_prefix: 2 digit
        @return: Postcodes starting with the prefix with no address areas
        """
        return united_states_companies.filter(
            address_postcode__startswith=zip_prefix,
            address_area_id__isnull=True,
        )

    def us_administrative_area_by_code(self, area_code):
        """
        Gets United States Administrative Area by Area Code
        @param area_code:
        @return: First Administrative Area Found
        """
        return AdministrativeArea.objects.filter(
            country_id=Country.united_states.value.id,
            area_code=area_code,
        ).first()

    def update_address_postcode(self):
        """
        Update address postcodes where the subquery exists
        """
        Company.objects.filter(
            address_country=Country.united_states.value.id,
        ).update(
            address_postcode=Func(
                F('address_postcode'),
                Value(Country.united_states.value.postcode_pattern),
                Value(Country.united_states.value.postcode_replacement),
                Value('gm'),
                function='regexp_replace',
            ),
        )

    def update_registered_address_postcode(self):
        """
        Update registered address postcodes where the subquery exists
        """
        Company.objects.filter(
            address_country=Country.united_states.value.id,
        ).update(
            registered_address_postcode=Func(
                F('registered_address_postcode'),
                Value(Country.united_states.value.postcode_pattern),
                Value(Country.united_states.value.postcode_replacement),
                Value('gm'),
                function='regexp_replace',
            ),
        )
