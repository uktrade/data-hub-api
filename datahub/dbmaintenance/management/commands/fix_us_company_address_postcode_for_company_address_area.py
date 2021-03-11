from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from django.db.models import F, Func, Value

from datahub.company.models import Company
from datahub.core.constants import US_ZIP_STATES
from datahub.metadata.models import AdministrativeArea

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to query for the ids of duns-linked companies for a particular set of
    one list tiers and (optionally) particular set of account managers.
    Example of executing this command locally:
        python manage.py fix_us_company_address_postcode_data
    """

    # Visualise this @ https://regex101.com/r/yckIVj/3
    US_POST_CODE_PATTERN = r'^.*?(?:(\d{5}-\d{4})|(\d{5}\s-\s\d{4})' \
                           r'|(\d{5}\s–\s\d{4})|(\d{9})|(\d)\s?(\d{4})).*?$'
    UNITED_STATES_ID = '81756b9a-5d95-e211-a939-e4115bead28a'
    REPLACEMENT = r'\1\2\3\4\5\6'
    REGEX_OPTIONS = 'gm'

    def add_arguments(self, parser):
        """
        No arguments needed for the management command.
        """
        pass

    def handle(self, *args, **options):
        """
        Run the query and output the results as an info message to the log file.
        """
        Command.fix_postcodes_and_address_areas()

    @staticmethod
    def fix_postcodes_and_address_areas():
        """
        Does update on the postcode address table
        """
        with reversion.create_revision():
            Command.update_address_postcode()
            Command.update_registered_address_postcode()
            reversion.set_comment('Address Postcode Fix.')

        with reversion.create_revision():
            Command.update_address_area()
            reversion.set_comment('Company Address Area Migration')

        with reversion.create_revision():
            Command.update_registered_address_area()
            reversion.set_comment('Company Registered Address Area Migration')

    @staticmethod
    def update_registered_address_area():
        """
        Update company registered address area data
        """
        united_states_companies = Company \
            .objects \
            .filter(registered_address_country=Command.UNITED_STATES_ID)

        for zip_prefix, area_code, _area_name in US_ZIP_STATES:
            administrative_area = Command.us_administrative_area_by_code(area_code)
            Command.no_area_companies_by_registered_address_postcode(
                united_states_companies,
                zip_prefix,
            ). \
                update(registered_address_area_id=administrative_area.id)

    @staticmethod
    def update_address_area():
        """
        Update company address area data
        """
        united_states_companies = Company\
            .objects\
            .filter(address_country=Command.UNITED_STATES_ID)

        for zip_prefix, area_code, _area_name in US_ZIP_STATES:
            administrative_area = Command.us_administrative_area_by_code(area_code)
            Command.no_area_companies_by_address_postcode(
                united_states_companies,
                zip_prefix,
            ).\
                update(address_area_id=administrative_area.id)

    @staticmethod
    def no_area_companies_by_registered_address_postcode(united_states_companies, zip_prefix):
        """
        Filters United States Countries by registered address postcode equal to zip-prefix
        where no registered address area exists
        @param united_states_companies: united states company query
        @param zip_prefix: 3 digit zip prefix
        @return: Filtered Company
        """
        return united_states_companies.filter(
            registered_address_postcode__startswith=zip_prefix,
            registered_address_area_id__isnull=True,
        )

    @staticmethod
    def no_area_companies_by_address_postcode(united_states_companies, zip_prefix):
        """
        Filters United States Countries by address postcode equal to zip-prefix
        where no address area exists
        @param united_states_companies: united states company query
        @param zip_prefix: 2 digit
        @return:
        """
        return united_states_companies.filter(
            address_postcode__startswith=zip_prefix,
            address_area_id__isnull=True,
        )

    @staticmethod
    def us_administrative_area_by_code(area_code):
        """
        Gets United States Administrative Area by Area Code
        @param area_code:
        @return:First Administrative Area Found
        """
        return AdministrativeArea.objects.filter(
            country_id=Command.UNITED_STATES_ID,
            area_code=area_code,
        ).first()

    @staticmethod
    def update_address_postcode():
        """
        Update address postcodes where the subquery exists
        """
        Company \
            .objects \
            .filter(address_country=Command.UNITED_STATES_ID) \
            .update(
                address_postcode=Func(
                    F('address_postcode'),
                    Value(Command.US_POST_CODE_PATTERN),
                    Value(Command.REPLACEMENT),
                    Value(Command.REGEX_OPTIONS),
                    function='regexp_replace'))

    @staticmethod
    def update_registered_address_postcode():
        """
        Update registered address postcodes where the subquery exists
        """
        Company \
            .objects \
            .filter(address_country=Command.UNITED_STATES_ID) \
            .update(
                registered_address_postcode=Func(
                    F('registered_address_postcode'),
                    Value(Command.US_POST_CODE_PATTERN),
                    Value(Command.REPLACEMENT),
                    Value(Command.REGEX_OPTIONS),
                    function='regexp_replace'))
