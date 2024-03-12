from decimal import Decimal, ROUND_HALF_UP
from logging import getLogger

from django.utils.functional import cached_property

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
)
from datahub.core.constants import (
    InvestmentType as InvestmentTypeConstant,
    Sector as SectorConstant,
)
from datahub.investment.project.models import GVAMultiplier

logger = getLogger(__name__)


class GrossValueAddedCalculator:
    """Gross Value Added (GVA) Calculator.

    This calculates the Gross Value Added for an investment project.

    A project must meet the following criteria to be able to generate its GVA:

    - Must be an FDI project
    - Must have either a sector set or a business activity of retail or sales
    - Must have a value for foreign equity investment
    - Must have a value for number of new jobs

    Using the sector/business activity a GVA multiplier for financial year associated with
    the sector is retrieved. This multiplier is then multiplied by the foreign
    equity investment amount or number of jobs depending on the sector classification.
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
        if self.gva_multiplier is None:
            return None
        if (
            self.gva_multiplier.sector_classification_gva_multiplier
            == GVAMultiplier.SectorClassificationChoices.CAPITAL
        ):
            if self.investment_project.foreign_equity_investment is None:
                return None
            return Decimal(
                self.gva_multiplier.multiplier
                * self.investment_project.foreign_equity_investment,
            ).quantize(
                Decimal('1.'),
                rounding=ROUND_HALF_UP,
            )
        if (
            self.gva_multiplier.sector_classification_gva_multiplier
            == GVAMultiplier.SectorClassificationChoices.LABOUR
        ):
            if self.investment_project.number_new_jobs is None:
                return None
            return Decimal(
                self.gva_multiplier.multiplier
                * self.investment_project.number_new_jobs,
            ).quantize(
                Decimal('1.'),
                rounding=ROUND_HALF_UP,
            )
        return None

    def _get_gva_multiplier_for_investment_project(self):
        """:returns a GVA multiplier for an investment project."""
        if (
            str(self.investment_project.investment_type_id)
            != InvestmentTypeConstant.fdi.value.id
        ):
            return None

        if self._has_business_activity_of_retail_or_sales():
            return self._get_retail_gva_multiplier()

        if self.investment_project.sector:
            return self._get_sector_gva_multiplier()
        else:
            return None

    def _has_business_activity_of_retail_or_sales(self):
        """:returns True or False. Checks if an investment project has either a
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
        return self._get_gva_multiplier(SectorConstant.consumer_and_retail.value.id)

    def _get_sector_gva_multiplier(self):
        """:returns the GVA Multiplier for a sector."""
        return self._get_gva_multiplier(self.investment_project.sector.id)

    def _get_gva_multiplier(self, sector_id):
        """:returns a GVA Multiplier or None.

        Retrieves all the GVA multipliers for a sector in descending order.
        Returns the first instance (i.e. latest GVA multiplier) if there is one.

        If there are no multipliers for a given sector, returns None.

        """
        gva_multipliers_for_sector = GVAMultiplier.objects.filter(
            sector_id=sector_id,
        ).order_by(
            '-financial_year',
        )
        if gva_multipliers_for_sector.first() is None:
            logger.exception(
                f'Unable to find GVA multiplier for sector {sector_id}',
            )
        return gva_multipliers_for_sector.first()


def set_gross_value_added_for_investment_project(investment_project):
    """Sets the Gross Value Added data for investment project."""
    calculate_gross_value_added = GrossValueAddedCalculator(investment_project)
    investment_project.gva_multiplier = calculate_gross_value_added.gva_multiplier
    investment_project.gross_value_added = calculate_gross_value_added.gross_value_added
    return investment_project
