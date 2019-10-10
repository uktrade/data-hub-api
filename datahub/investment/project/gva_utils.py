from datetime import datetime
from logging import getLogger
from math import ceil

from django.utils.functional import cached_property

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.core.utils import get_financial_year
from datahub.investment.project.constants import (
    FDISICGrouping as FDI_SICGroupingConstant,
)
from datahub.investment.project.models import GVAMultiplier, InvestmentSector

logger = getLogger(__name__)


class GrossValueAddedCalculator:
    """
    Gross Value Added (GVA) Calculator.

    This calculates the Gross Value Added for an investment project.

    A project must meet the following criteria to be able to generate its GVA:

    - Must be an FDI project
    - Must have either a sector set or a business activity of retail
    - Must have a value for foreign equity investment

    Using the sector/business activity a GVA multiplier for financial year associated with
    the sector is retrieved. This multiplier is then multiplied by the
    foreign equity investment amount.
    """

    def __init__(self, investment_project):
        """Sets the investment project."""
        self.investment_project = investment_project

    @cached_property
    def gva_multiplier(self):
        """:returns the GVA multiplier if one is found."""
        return self._get_gva_multiplier_for_investment_project()

    @cached_property
    def gross_value_added(self):
        """Calculates the Gross Value Added (GVA) for an investment project."""
        if not self.investment_project.foreign_equity_investment or not self.gva_multiplier:
            return None
        return ceil(
            self.gva_multiplier.multiplier * self.investment_project.foreign_equity_investment,
        )

    def _get_gva_multiplier_for_investment_project(self):
        """:returns a GVA multiplier for an investment project."""
        if str(self.investment_project.investment_type_id) != InvestmentTypeConstant.fdi.value.id:
            return None

        if self._has_business_activity_of_retail_or_sales():
            return self._get_retail_gva_multiplier()

        if self.investment_project.sector:
            return self._get_sector_gva_multiplier()
        else:
            return None

    def _has_business_activity_of_retail_or_sales(self):
        """
        :returns True or False. Checks if an investment project has either a
        business activity of retail or sales.
        """
        return self.investment_project.business_activities.filter(
            id__in=[
                InvestmentBusinessActivityConstant.retail.value.id,
                InvestmentBusinessActivityConstant.sales.value.id,
            ],
        ).exists()

    def _get_retail_gva_multiplier(self):
        """:returns the GVA Multiplier for a retail investment project."""
        return self._get_gva_multiplier(FDI_SICGroupingConstant.retail.value.id)

    def _get_sector_gva_multiplier(self):
        """:returns the GVA Multiplier for the a sector if one found else returns None."""
        fdi_sic_grouping = self._get_fdi_sic_grouping_for_sector()
        if not fdi_sic_grouping:
            return None
        return self._get_gva_multiplier(fdi_sic_grouping.id)

    def _get_fdi_sic_grouping_for_sector(self):
        """:returns the FDI SIC Grouping for a DIT Sector if one found else returns None."""
        root_sector = self.investment_project.sector.get_root()
        investment_sector = self._get_investment_sector(root_sector)
        if not investment_sector:
            return None
        return investment_sector.fdi_sic_grouping

    def _get_gva_multiplier(self, fdi_sic_grouping_id):
        """
        :returns a GVA Multiplier or None.

        Firstly retrieves all the GVA Multipliers for a FDI SIC Grouping. Then checks
        if there is a multiplier for the given financial year. If one is not found
        then returns the GVA Multiplier for the last year there is an entry for.

        GVA multipliers will be reviewed each year to ensure they continue to be accurate with
        a changing economy. If the GVA values have not been updated, the latest year's information
        should continue to be used as it represents the most accurate data available

        If there are no entries returns None.

        """
        gva_multipliers_for_grouping = GVAMultiplier.objects.filter(
            fdi_sic_grouping_id=fdi_sic_grouping_id,
        ).order_by(
            '-financial_year',
        )

        financial_year = self._get_gva_multiplier_financial_year()
        try:
            return gva_multipliers_for_grouping.get(
                financial_year=financial_year,
            )
        except GVAMultiplier.DoesNotExist:
            if gva_multipliers_for_grouping.filter(
                financial_year__gt=financial_year,
            ).exists():
                logger.exception(
                    f'Unable to find a GVA Multiplier for financial year {financial_year} '
                    f'fdi sic grouping id {fdi_sic_grouping_id}',
                )
            return gva_multipliers_for_grouping.first()

    def _get_investment_sector(self, root_sector):
        """:returns the investment sector for a root DIT sector if one found else returns None."""
        try:
            return root_sector.investmentsector
        except InvestmentSector.DoesNotExist:
            logger.warning(
                f'Unable to find InvestmentSector for DIT Sector {root_sector}',
            )
            return None

    def _get_gva_multiplier_financial_year(self):
        """
        :returns the financial year that should be used for the investment project.

        If the investment project does not have an actual land date return the current
        financial year. If the actual land date is less than or equal to 2019 return 2019
        this is because there is no multiplier data prior to the 2019 financial year.

        Due to the multiplier data being for a financial year for all investment projects
        with actual land date greater than 2019 return the financial year that the project landed.
        """
        if not self.investment_project.actual_land_date:
            return get_financial_year(
                datetime.today(),
            )

        return max(
            get_financial_year(self.investment_project.actual_land_date),
            2019,
        )


def set_gross_value_added_for_investment_project(investment_project):
    """Sets the Gross Value Added data for investment project."""
    calculate_gross_value_added = GrossValueAddedCalculator(investment_project)
    investment_project.gva_multiplier = calculate_gross_value_added.gva_multiplier
    investment_project.gross_value_added = calculate_gross_value_added.gross_value_added
    return investment_project
