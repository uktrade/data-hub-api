from datetime import date
from decimal import Decimal
from unittest import mock

import pytest

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
    Sector as SectorConstant,
)
from datahub.investment.project.constants import FDISICGrouping as FDISICGroupingConstant
from datahub.investment.project.gva_utils import GrossValueAddedCalculator
from datahub.investment.project.models import GVAMultiplier
from datahub.investment.project.test.factories import (
    FDISICGroupingFactory,
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import SectorFactory


CAPITAL = GVAMultiplier.SectorClassificationChoices.CAPITAL
LABOUR = GVAMultiplier.SectorClassificationChoices.LABOUR

pytestmark = pytest.mark.django_db


class TestGrossValueAddedCalculator:
    """Test for Gross Value Added Calculator."""

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities,expected_multiplier_value',
        [
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [],
                None,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                ],
                '51983.514030000',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.sales.value.id,
                ],
                '51983.514030000',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.sales.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,

                ],
                '51983.514030000',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                '0.093757195',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.aerospace_assembly_aircraft.value.id,
                [],
                '0.209650945',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                '51983.514030000',
            ),
            (
                InvestmentTypeConstant.commitment_to_invest.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                None,
            ),
            (
                InvestmentTypeConstant.non_fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                ],
                None,
            ),
        ],
    )
    def test_set_gva_multiplier(
        self,
        investment_type,
        sector,
        business_activities,
        expected_multiplier_value,
    ):
        """Test the GVA Multiplier correctly gets set on an investment project."""
        project = InvestmentProjectFactory(
            sector_id=sector,
            business_activities=business_activities,
            investment_type_id=investment_type,
        )
        if not expected_multiplier_value:
            assert not project.gva_multiplier
        else:
            assert project.gva_multiplier.multiplier == Decimal(expected_multiplier_value)

    def test_multiple_gva_multipliers_for_sector_returns_most_recent_multiplier(self):
        """
        Test when multiple GVA multipliers are present for a sector, it returns the
        most recent multiplier.
        """
        sector_id = SectorConstant.renewable_energy_wind.value.id
        fdi_sic_grouping_id = FDISICGroupingConstant.electric.value.id
        GVAMultiplierFactory(
            financial_year=2030,
            sector_id=sector_id,
            fdi_sic_grouping_id=fdi_sic_grouping_id,
        )
        GVAMultiplierFactory(
            financial_year=2040,
            sector_id=sector_id,
            fdi_sic_grouping_id=fdi_sic_grouping_id,
        )
        project = InvestmentProjectFactory(
            sector_id=sector_id,
            business_activities=[],
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            foreign_equity_investment=1000,
        )
        assert project.gva_multiplier.financial_year == 2040

    def test_no_gva_multiplier_found_for_sector_returns_none(self, caplog):
        """
        Test when a GVA Multiplier is not present for the given sector.
        Checks an exception is added to the log to flag that data is missing.
        """
        caplog.set_level('WARNING')
        sector = SectorFactory()
        project = InvestmentProjectFactory(
            sector_id=sector.id,
            business_activities=[],
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            foreign_equity_investment=1000,
            actual_land_date=date(2050, 5, 1),

        )
        assert project.gva_multiplier is None
        assert caplog.messages[0] == (
            f'Unable to find GVA multiplier for sector {sector.id}'
        )

    def test_no_foreign_equity_investment_on_capital_intensive_project_returns_none(self):
        """
        Tests when an investment project has no foreign equity investment,
        and sector is capital intensive, that it returns a GVA value of none.
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        GVAMultiplierFactory(
            fdi_sic_grouping_id=fdi_sic_grouping.id,
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=GVAMultiplier.SectorClassificationChoices.CAPITAL,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=None,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=200,
            sector_id=sector.id,
        )
        assert project.gross_value_added is None

    def test_no_foreign_equity_investment_on_labour_intensive_project_returns_value(self):
        """
        Tests when an investment project has no foreign equity investment,
        and the sector is labour intensive, that it still returns a GVA value.
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        gva_multiplier = GVAMultiplierFactory(
            fdi_sic_grouping_id=fdi_sic_grouping.id,
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=GVAMultiplier.SectorClassificationChoices.LABOUR,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=None,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=200,
            sector_id=sector.id,
        )
        expected_gva_value = gva_multiplier.multiplier * project.number_new_jobs
        assert project.gross_value_added == Decimal(expected_gva_value)

    def test_no_number_of_jobs_on_capital_intensive_project_returns_value(self):
        """
        Tests when an investment project has no number of new jobs,
        and sector is capital intensive, that it still returns a GVA value.
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        gva_multiplier = GVAMultiplierFactory(
            fdi_sic_grouping_id=fdi_sic_grouping.id,
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=GVAMultiplier.SectorClassificationChoices.CAPITAL,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=1000,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=None,
            sector_id=sector.id,
        )
        expected_gva_value = gva_multiplier.multiplier * project.foreign_equity_investment
        assert project.gross_value_added == Decimal(expected_gva_value)

    def test_no_number_of_jobs_on_labour_intensive_project_returns_none(self):
        """
        Tests when an investment project has no number of jobs,
        and the sector is labour intensive, that it returns none.
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        GVAMultiplierFactory(
            fdi_sic_grouping_id=fdi_sic_grouping.id,
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=GVAMultiplier.SectorClassificationChoices.LABOUR,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=1000,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=None,
            sector_id=sector.id,
        )
        assert project.gross_value_added is None

    def test_no_gva_multiplier_returns_none(self):
        """
        Tests if a project's GVA multiplier is none, that it returns a GVA value of none.
        """
        project = InvestmentProjectFactory()
        project.gva_multiplier = None
        assert project.gross_value_added is None

    def test_if_capital_intensive_gva_value_is_multiplier_times_fei(self):
        """
        Tests the GVA value for a capital intensive project is calculated using
        the formula: gva value = multiplier * foreign equity investment (fei).
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        gva_multiplier = GVAMultiplierFactory(
            fdi_sic_grouping_id=fdi_sic_grouping.id,
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=GVAMultiplier.SectorClassificationChoices.CAPITAL,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=1200,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=200,
            sector_id=sector.id,
        )
        expected_gva_value = gva_multiplier.multiplier * project.foreign_equity_investment
        assert project.gross_value_added == Decimal(expected_gva_value)

    def test_if_labour_intensive_gva_value_is_multiplier_times_jobs(self):
        """
        Tests the GVA value for a labour intensive project is calculated using
        the formula: gva value = multiplier * number of jobs.
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        gva_multiplier = GVAMultiplierFactory(
            fdi_sic_grouping_id=fdi_sic_grouping.id,
            multiplier=0.5,
            sector_id=sector.id,
            sector_classification_gva_multiplier=GVAMultiplier.SectorClassificationChoices.LABOUR,
        )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=1200,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=200,
            sector_id=sector.id,
        )
        expected_gva_value = gva_multiplier.multiplier * project.number_new_jobs
        assert project.gross_value_added == Decimal(expected_gva_value)

    @pytest.mark.parametrize(
        'foreign_equity_investment, number_new_jobs,sector_classification, multiplier_value, expected_gva',  # noqa
        [
            (1200, 200, CAPITAL, 0.5, 600),  # Capital intensive
            (1200, 200, LABOUR, 0.5, 100),   # Labour intensive
            (None, 200, CAPITAL, 0.5, None),  # Capital intensive, no FEI
            (1200, None, LABOUR, 0.5, None),  # Labour intensive, no jobs
            (100000, 50, CAPITAL, None, None),  # Capital intensive, no GVA multiplier
            (130000000, 1000, LABOUR, None, None),  # Labour intensive, no GVA multiplier
            (5000000, 100, CAPITAL, 0.07, 350000),  # Capital intensive, large investment
            (2000000, 500, LABOUR, 0.15, 75),  # Labour intensive, moderate number of jobs
            (0, 100, CAPITAL, 0.1, 0),  # Capital intensive, zero investment
            (1000000, 0, LABOUR, 0.05, 0),  # Labour intensive, zero jobs
            # Capital intensive, very large investment
            (999999999999991, 1000, CAPITAL, 1, '999999999999991'),
            # Labour intensive, minimal jobs; expected value is 0 due to rounding
            (150000, 1, LABOUR, 0.25, 0),
            (1200, 200, 'another', 0.5, None),  # Neither labour or capital intensive
        ],
    )
    def test_calculate_gva(
        self,
        foreign_equity_investment,
        number_new_jobs,
        sector_classification,
        multiplier_value,
        expected_gva,
    ):
        """
        Test various scenarios for correct GVA calculation.
        """
        sector = SectorFactory()
        fdi_sic_grouping = FDISICGroupingFactory()
        if multiplier_value is None:
            # avoids violating GVAMultiplier's not-null constraint
            gva_multiplier = None
        else:
            gva_multiplier = GVAMultiplierFactory(
                fdi_sic_grouping_id=fdi_sic_grouping.id,
                multiplier=multiplier_value,
                sector_id=sector.id,
                sector_classification_gva_multiplier=sector_classification,
            )
        project = InvestmentProjectFactory(
            business_activities=[],
            foreign_equity_investment=foreign_equity_investment,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            number_new_jobs=number_new_jobs,
            sector_id=sector.id,
        )
        with mock.patch(
            'datahub.investment.project.gva_utils.GrossValueAddedCalculator._get_gva_multiplier_for_investment_project',  # noqa
            return_value=gva_multiplier,
        ):
            calculated_gva = GrossValueAddedCalculator(project).gross_value_added
            if expected_gva is not None:
                assert calculated_gva == Decimal(expected_gva)
            else:
                assert calculated_gva is None

    def test_presence_of_gva_multipliers_for_each_sector(self):
        """
        Tests that all sectors have an associated GVA multiplier.
        """
        sector_ids = [
            sector.id for sector
            in Sector.objects.all()
            if not sector.disabled_on
        ]
        gva_multiplier_sector_ids = [
            gva_multiplier.sector.id for gva_multiplier
            in GVAMultiplier.objects.all()
        ]
        assert set(sector_ids) == set(gva_multiplier_sector_ids)
