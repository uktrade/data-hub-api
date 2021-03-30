import re
from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.company.models import Company
from datahub.core.constants import Country, US_ZIP_STATES
from datahub.metadata.models import AdministrativeArea

logger = getLogger(__name__)


def is_empty_or_space(value):
    """
    Checks a string to see if it is None or has whitespace
    @param value:
    @return:
    """
    if not type(value) is str:
        raise TypeError('Only strings supported')
    return not (value and not value.isspace())


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
        with reversion.create_revision():
            self.fix_postcodes_and_areas()
            reversion.set_comment('US Area and postcode Fix.')

    def fix_postcodes_and_areas(self):
        """
        Does update on the postcode address table
        """
        for us_company in self.us_companies_with_no_areas():
            if self.fix_address_postcode(us_company):
                area_code = self.get_area_code(us_company.address_postcode)
                self.update_address_area(area_code, us_company)
            if self.fix_registered_address_postcode(us_company):
                area_code = self.get_area_code(us_company.address_postcode)
                self.update_registered_address_area(area_code, us_company)

    def us_companies_with_no_areas(self):
        """United states companies"""
        query = Q(address_area_id__isnull=True,)
        query.add(Q(registered_address_area_id__isnull=True,), Q.OR)
        query.add(Q(address_country=Country.united_states.value.id), Q.AND)
        return Company.objects.filter(query)

    def update_address_area(self, area_code, us_company):
        """
        Update address area with administrative area
        @param area_code:
        @param us_company:
        @return:
        """
        if area_code:
            administrative_area = self.us_administrative_area_by_code(area_code)
            if administrative_area:
                us_company.address_area_id = administrative_area.id
                us_company.save(force_update=True)
                logger.info(f'Updated address area by "{area_code}"')

    def update_registered_address_area(self, area_code, us_company):
        """
        Update registered address area with administrative area
        @param area_code:
        @param us_company:
        @return:
        """
        if area_code:
            administrative_area = self.us_administrative_area_by_code(area_code)
            if administrative_area:
                us_company.registered_address_area_id = administrative_area.id
                us_company.save(force_update=True)
                logger.info(f'Updated registered address area by "{area_code}"')

    def get_area_code(self, post_code):
        """
        Get area code from a postcode
        @param post_code: Post Code from an address
        @return: An area code based on the format states list
        """
        if post_code:
            for zip_prefix, area_code, _area_name in US_ZIP_STATES:
                if post_code.startswith(zip_prefix):
                    return area_code
        return None

    def fix_address_postcode(self, us_company):
        """
        Fix address postcode formatting the postcode into an expected format if possible
        @param us_company:
        """
        if not is_empty_or_space(us_company.address_postcode) and us_company.address_area is None:
            logger.info(f'Updating address postcode from "{us_company.address_postcode}"')
            us_company.address_postcode = re.sub(
                Country.united_states.value.postcode_pattern,
                Country.united_states.value.postcode_replacement,
                us_company.address_postcode,
                0,
                re.MULTILINE,
            )
            logger.info(f'to address postcode "{us_company.address_postcode}"')
            us_company.save(force_update=True)
            return True
        return False

    def fix_registered_address_postcode(self, us_company):
        """
        Fix registered address postcode formatting the postcode into an expected format if possible
        @param us_company:
        """
        if not is_empty_or_space(us_company.registered_address_postcode) and \
                us_company.registered_address_area is None:
            logger.info(f'Updating registered postcode from "{us_company.address_postcode}"')
            us_company.registered_address_postcode = re.sub(
                Country.united_states.value.postcode_pattern,
                Country.united_states.value.postcode_replacement,
                us_company.registered_address_postcode,
                0,
                re.MULTILINE,
            )
            logger.info(f'to registered postcode "{us_company.registered_address_postcode}"')
            us_company.save(force_update=True)
            return True
        return False

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
