import re
from logging import getLogger

import reversion
from django.db.models import Q

from datahub.company.models import Company
from datahub.core.validate_utils import is_not_blank
from datahub.metadata.models import AdministrativeArea

logger = getLogger(__name__)


class CompanyAddressResolver:
    """
    Command for resolving company address postcode and areas
    """

    def __init__(
        self,
        country_id,
        revision_comment,
        zip_states,
        postcode_replacement,
    ):
        """
        Fixing Company address areas by country
        :param country_id: Country identifier associated with the address
        being resolved
        :param revision_comment: Comment for audit purpose
        :param zip_states: This is a unique list of postcode prefixes or
        identifiers facilitating area mapping
        :param postcode_replacement: Regex patterns to regulate postcode
        replacement
        """
        self.country_id = country_id
        self.revision_comment = revision_comment
        self.postcode_replacement = postcode_replacement
        self.zip_states = zip_states

    def get_companies_with_no_areas(self):
        """Companies with no areas and country
        or no registered areas and registered country
        and not archived with a duns value to guarantee the quality of the data
        """
        result = Company.objects.filter(
            Q(
                Q(
                    Q(address_area_id__isnull=True)
                    & Q(address_country=self.country_id),
                )
                | Q(
                    Q(registered_address_area_id__isnull=True)
                    & Q(registered_address_country=self.country_id),
                ),
            )
            & Q(
                Q(archived=False)
                & Q(duns_number__isnull=False),
            ),
        )
        return result

    def update_registered_address_area(self, area_code, company):
        """
        Update registered address area with administrative area
        :param area_code: Area code value
        :param company: Company data
        """
        if area_code and self.is_valid_postcode_format(company.registered_address_postcode):
            administrative_area = self.get_administrative_area_by_code(area_code)
            company.registered_address_area_id = administrative_area.id
            company.save(force_update=True)
            logger.info(
                f'Updated registered area "{area_code}"',
                f' for "{company.registered_address_postcode}"',
            )

    def fix_address_postcode(self, company):
        """
        Fix address postcode formatting the postcode into an expected format if possible
        :param company: Company record
        """
        if is_not_blank(company.address_postcode):
            log_message = f'Updating address postcode from "{company.address_postcode}"'
            company.address_postcode = self.format_postcode(company.address_postcode)
            logger.info(f'{log_message} to address postcode "{company.address_postcode}"')
            company.save(force_update=True)
            return True
        return False

    def fix_postcodes_and_areas(self):
        """
        Does update on the postcode address table
        """
        for company in self.get_companies_with_no_areas():
            if self.fix_address_postcode(company):
                area_code = self.get_area_code(company.address_postcode)
                self.update_address_area(area_code, company)
            if self.fix_registered_address_postcode(company):
                area_code = self.get_area_code(company.registered_address_postcode)
                self.update_registered_address_area(area_code, company)

    def run(self):
        """
        Run the query and output the results as an info message to the log file.
        """
        with reversion.create_revision():
            self.fix_postcodes_and_areas()
            reversion.set_comment(self.revision_comment)

    def update_address_area(self, area_code, company):
        """
        Update address area with administrative area
        :param area_code: Area code value
        :param company: Company data
        """
        if area_code and self.is_valid_postcode_format(company.address_postcode):
            administrative_area = self.get_administrative_area_by_code(area_code)
            company.address_area_id = administrative_area.id
            company.save(force_update=True)
            logger.info(f'Updated area "{area_code}" for "{company.address_postcode}"')

    def get_area_code(self, post_code):
        """
        Get area code from a postcode
        :param post_code: Post Code from an address
        :return: An area code based on the format states list
        """
        if is_not_blank(post_code):
            for zip_prefix, area_code, _area_name in self.zip_states:
                if post_code.startswith(zip_prefix):
                    return area_code
        return None

    def format_postcode(self, postcode):
        """
        Format postcode with postcode pattern for united states
        :param postcode: Postcode string value
        :return: Formatted US postcode value
        """
        return re.sub(
            self.postcode_replacement.postcode_pattern,
            self.postcode_replacement.postcode_replacement,
            postcode,
            0,
            re.MULTILINE,
        )

    def is_valid_postcode_format(self, postcode):
        """
        Validates the postcode is valid based one the postcode replacement regex
        :param postcode: Address Postcode
        :return: True if valid, False if Invalid
        """
        return re.fullmatch(self.postcode_replacement.postcode_pattern, postcode, re.MULTILINE)

    def fix_registered_address_postcode(self, company):
        """
        Fix registered address postcode formatting the postcode into an expected format if possible
         :param company: company record
        """
        if is_not_blank(company.registered_address_postcode):
            log_message = (
                f'Updating registered postcode from "{company.registered_address_postcode}"'
            )
            company.registered_address_postcode = self.format_postcode(
                company.registered_address_postcode,
            )
            logger.info(
                f'{log_message} to registered postcode ',
                f'"{company.registered_address_postcode}"',
            )
            company.save(force_update=True)
            return True
        return False

    def get_administrative_area_by_code(self, area_code):
        """
        Gets United States Administrative Area by Area Code
        :param area_code: Unique ISO administrative area code
        :return: First Administrative Area Found
        """
        return AdministrativeArea.objects.filter(
            country_id=self.country_id,
            area_code=area_code,
        ).first()
