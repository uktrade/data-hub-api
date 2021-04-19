import re
from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.company.models import Company
from datahub.core.constants import Country
from datahub.core.postcode_constants import CountryPostcodeReplacement, US_ZIP_STATES
from datahub.core.validate_utils import is_not_blank
from datahub.metadata.models import AdministrativeArea

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to make US postcodes conform to a standard format and update states
    accordingly.
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
        for us_company in self.get_us_companies_with_no_areas():
            if self.fix_address_postcode(us_company):
                area_code = self.get_area_code(us_company.address_postcode)
                self.update_address_area(area_code, us_company)
            if self.fix_registered_address_postcode(us_company):
                area_code = self.get_area_code(us_company.registered_address_postcode)
                self.update_registered_address_area(area_code, us_company)

    def get_us_companies_with_no_areas(self):
        """United states companies with no areas"""
        query = Q(address_area_id__isnull=True)
        query.add(Q(registered_address_area_id__isnull=True), Q.OR)
        query.add(Q(address_country=Country.united_states.value.id), Q.AND)
        query.add(Q(registered_address_country=Country.united_states.value.id), Q.OR)
        return Company.objects.filter(query)

    def update_address_area(self, area_code, us_company):
        """
        Update address area with administrative area
        :param area_code: Area code value
        :param us_company: United States Company data
        """
        if area_code:
            administrative_area = self.get_us_administrative_area_by_code(area_code)
            if administrative_area:
                us_company.address_area_id = administrative_area.id
                us_company.save(force_update=True)
                logger.info(f'Updated area "{area_code}" for "{us_company.address_postcode}"')

    def update_registered_address_area(self, area_code, us_company):
        """
        Update registered address area with administrative area
        :param area_code: Area code value
        :param us_company: United States Company data
        """
        if area_code:
            administrative_area = self.get_us_administrative_area_by_code(area_code)
            if administrative_area:
                us_company.registered_address_area_id = administrative_area.id
                us_company.save(force_update=True)
                logger.info(f'Updated registered area "{area_code}"'
                            f' for "{us_company.registered_address_postcode}"')

    def get_area_code(self, post_code):
        """
        Get area code from a postcode
        :param post_code: Post Code from an address
        :return: An area code based on the format states list
        """
        if post_code:
            for zip_prefix, area_code, _area_name in US_ZIP_STATES:
                if post_code.startswith(zip_prefix):
                    return area_code
        return None

    def fix_address_postcode(self, us_company):
        """
        Fix address postcode formatting the postcode into an expected format if possible
        :param us_company: United States company record
        """
        if is_not_blank(us_company.address_postcode):
            log_message = f'Updating address postcode from "{us_company.address_postcode}"'
            us_company.address_postcode = self.format_postcode(us_company.address_postcode)
            logger.info(f'{log_message} to address postcode "{us_company.address_postcode}"')
            us_company.save(force_update=True)
            return True
        return False

    def fix_registered_address_postcode(self, us_company):
        """
        Fix registered address postcode formatting the postcode into an expected format if possible
         :param us_company: United States company record
        """
        if is_not_blank(us_company.registered_address_postcode):
            log_message = f'Updating registered postcode ' \
                          f'from "{us_company.registered_address_postcode}"'
            us_company.registered_address_postcode = self.format_postcode(
                us_company.registered_address_postcode)
            logger.info(f'{log_message} to registered postcode '
                        f'"{us_company.registered_address_postcode}"')
            us_company.save(force_update=True)
            return True
        return False

    def format_postcode(self, postcode):
        """
        Format postcode with postcode pattern for united states
        :param postcode: Postcode string value
        :return: Formatted US postcode value
        """
        return re.sub(
            CountryPostcodeReplacement.united_states.value.postcode_pattern,
            CountryPostcodeReplacement.united_states.value.postcode_replacement,
            postcode,
            0,
            re.MULTILINE,
        )

    def get_us_administrative_area_by_code(self, area_code):
        """
        Gets United States Administrative Area by Area Code
        :param area_code: Unique ISO administrative area code
        :return: First Administrative Area Found
        """
        return AdministrativeArea.objects.filter(
            country_id=Country.united_states.value.id,
            area_code=area_code,
        ).first()
