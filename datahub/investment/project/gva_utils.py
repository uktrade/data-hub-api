from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.investment.project.constants import (
    FDISICGrouping as FDI_SICGroupingConstant,
)
from datahub.investment.project.models import GVAMultiplier


class CalculateGrossValueAdded:
    """Calculate Gross Value Added (GVA)."""

    def __init__(self, investment_project):
        """Sets the investment project and cache value for the gva multiplier."""
        self.investment_project = investment_project
        self._gva_multiplier = None

    @property
    def gva_multiplier(self):
        """:returns the GVA multiplier if one is found."""
        if self._gva_multiplier:
            return self._gva_multiplier
        self._gva_multiplier = self._get_gva_multiplier_for_investment_project()
        return self._gva_multiplier

    @property
    def gross_value_added(self):
        """Calculates the Gross Value Added (GVA) for an investment project."""
        if not self.investment_project.foreign_equity_investment or not self.gva_multiplier:
            return
        return round(
            self.gva_multiplier.multiplier * float(
                self.investment_project.foreign_equity_investment,
            ),
        )

    def _get_gva_multiplier_for_investment_project(self):
        """:returns a GVA multiplier for an investment project."""
        if str(self.investment_project.investment_type_id) != InvestmentTypeConstant.fdi.value.id:
            return
        if self.investment_project.business_activities.filter(
            id=InvestmentBusinessActivityConstant.retail.value.id,
        ).exists():
            return self._get_retail_gva_multiplier()
        if self.investment_project.sector:
            return self._get_sector_gva_multiplier()

    def _get_retail_gva_multiplier(self):
        """:returns the GVA Multiplier for a retail investment project."""
        return self._get_gva_multiplier(FDI_SICGroupingConstant.retail.value.id)

    def _get_sector_gva_multiplier(self):
        """:returns the GVA Multiplier for the a sector."""
        fdi_sic_grouping = self._get_fid_sic_grouping_for_sector()
        if not fdi_sic_grouping:
            return
        return self._get_gva_multiplier(fdi_sic_grouping.id)

    def _get_fid_sic_grouping_for_sector(self):
        """:returns the FDI SIC Grouping for a DIT Sector."""
        root_sector = self.investment_project.sector.get_root()
        investment_sector = getattr(root_sector, 'investmentsector', None)
        if not investment_sector:
            return
        return investment_sector.fdi_sic_grouping

    def _get_gva_multiplier(self, fdi_sic_grouping_id):
        """:returns a GVA Sector"""
        try:
            return GVAMultiplier.objects.get(
                fdi_sic_grouping_id=fdi_sic_grouping_id,
                financial_year=self._get_gva_multiplier_financial_year(),
            )
        except GVAMultiplier.DoesNotExist:
            return

    def _get_gva_multiplier_financial_year(self):
        """
        TODO: Check the investment project actual land date and
        to future proof when new GVA multiplier data is added and when no
        GVA Multiplier data exists for a given year.

        :returns the financial year that should be used for the investment project.
        """
        return 2019


def update_gross_value_added_for_investment_project(investment_project):
    """Updates the Gross Value Added data for investment project."""
    calculate_gross_value_added = CalculateGrossValueAdded(investment_project)
    gva_multiplier = calculate_gross_value_added.gva_multiplier
    gva_multiplier_id = getattr(gva_multiplier, 'id', None)
    if gva_multiplier_id == investment_project.gva_multiplier_id:
        return
    investment_project.gva_multiplier_id = gva_multiplier_id
    investment_project.gross_value_added = calculate_gross_value_added.gross_value_added
    return investment_project
