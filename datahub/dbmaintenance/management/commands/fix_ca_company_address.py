
from logging import getLogger

from datahub.core.constants import Country
from datahub.core.postcode_constants import CA_ZIP_STATES, CountryPostcodeReplacement
from datahub.dbmaintenance.management.commands.base_fix_company_address \
    import BaseFixCompanyAddress

logger = getLogger(__name__)


class Command(BaseFixCompanyAddress):
    """
    Command to make CA postcodes conform to a standard format and update states
    accordingly.
    Example of executing this command locally:
        python manage.py fix_us_company_address_postcode_for_company_address_area
        or use the makefile for developers
    """

    help = 'Fix Canadian Company address postcodes for the purpose of setting address areas'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        """
        Base for initialising CA Company address fixes
        :param stdout: Inherited
        :param stderr: Inherited
        :param no_color: Inherited
        :param force_color: Inherited
        """
        super().__init__(
            Country.canada.value.id,
            'Canada area and postcode fix.',
            CA_ZIP_STATES,
            CountryPostcodeReplacement.canada.value,
            stdout,
            stderr,
            no_color,
            force_color)
        logger.debug(f'"{self.country_id}" - {self.revision_comment} with '
                     f'"{self.postcode_replacement}"')
