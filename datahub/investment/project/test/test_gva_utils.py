from datetime import date
from decimal import Decimal
from unittest import mock

import pytest
from freezegun import freeze_time

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
    Sector as SectorConstant,
)
from datahub.investment.project.constants import FDISICGrouping as FDISICGroupingConstant
from datahub.investment.project.gva_utils import GrossValueAddedCalculator
from datahub.investment.project.test.factories import (
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)
from datahub.metadata.test.factories import SectorFactory


pytestmark = pytest.mark.django_db


class TestGrossValueAddedCalculator:
    """Test for Gross Value Added Calculator."""

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities,expected_multiplier_value',
        (
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
                '0.0581',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.sales.value.id,
                ],
                '0.0581',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.sales.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,

                ],
                '0.0581',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                '0.0325',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.aerospace_assembly_aircraft.value.id,
                [],
                '0.0621',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                '0.0581',
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
        ),
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

    def test_no_investment_sector_linking_sector_to_fdi_sic_grouping_returns_none(self):
        """
        Tests that when there is no link between a dit sector and an
        fdi sic grouping None is returned.
        """
        new_sector = SectorFactory(parent=None)
        project = InvestmentProjectFactory(
            sector_id=new_sector.id,
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            business_activities=[],
        )
        assert project.gva_multiplier is None

    @freeze_time('2050-01-01 01:01:01')
    def test_no_gva_multiplier_for_financial_year_returns_latest_year(self):
        """
        Test when a GVA Multiplier is not present for the financial year 2050.
        """
        GVAMultiplierFactory(
            multiplier=Decimal('0.5'),
            financial_year=2040,
            fdi_sic_grouping_id=FDISICGroupingConstant.electric.value.id,
        )
        project = InvestmentProjectFactory(
            sector_id=SectorConstant.renewable_energy_wind.value.id,
            business_activities=[],
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            foreign_equity_investment=1000,
        )
        assert project.gva_multiplier.financial_year == 2040

    def test_no_gva_multiplier_for_financial_year_logs_if_later_multiplier_available(
        self,
        caplog,
    ):
        """
        Test when a GVA Multiplier is not present for the financial year 2050 but one is
        present for 2052. Checks a log is added to the exception log to flag
        that data is missing for that year.
        """
        caplog.set_level('WARNING')

        GVAMultiplierFactory(
            multiplier=Decimal('0.5'),
            financial_year=2052,
            fdi_sic_grouping_id=FDISICGroupingConstant.electric.value.id,
        )
        GVAMultiplierFactory(
            multiplier=Decimal('0.5'),
            financial_year=2049,
            fdi_sic_grouping_id=FDISICGroupingConstant.electric.value.id,
        )

        project = InvestmentProjectFactory(
            sector_id=SectorConstant.renewable_energy_wind.value.id,
            business_activities=[],
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            foreign_equity_investment=1000,
            actual_land_date=date(2050, 5, 1),
        )
        assert project.gva_multiplier.financial_year == 2052
        assert caplog.messages[0] == (
            'Unable to find a GVA Multiplier for financial year 2050'
            f' fdi sic grouping id {FDISICGroupingConstant.electric.value.id}'
        )

    @pytest.mark.parametrize(
        'foreign_equity_investment,multiplier_value,expected_gross_value_added',
        (
            (1, 1, '1'),
            (None, 1, None),
            (100000, 0.0581, '5810'),
            (130000000, 0.4537, '58981000'),
            (10000000, 0.0621, '621000'),
            (111000, 0.0621, '6894'),
            (9999999999999999999, 0.9999, '9999000000000000000'),
            (9999999999999999999, 9.999999, '99999990000000008192'),
            (296000, 0.0581, '17198'),
            (7002180, 0.0386, '270285'),
            (287732, 0.3939, '113338'),
            (1800000, 0.0264, '47520'),
            (28000, 0.021, '588'),
            (8907560, 0.9526, '8485342'),
            (16717, 0.0853, '1426'),
        ),
    )
    def test_calculate_gva(
        self,
        foreign_equity_investment,
        multiplier_value,
        expected_gross_value_added,
    ):
        """Test calculate GVA."""
        gva_multiplier = GVAMultiplierFactory(
            multiplier=multiplier_value,
            financial_year=1980,
        )

        with mock.patch(
            'datahub.investment.project.gva_utils.GrossValueAddedCalculator._get_gva_multiplier',
        ) as mock_get_multiplier:
            mock_get_multiplier.return_value = gva_multiplier
            project = InvestmentProjectFactory(
                foreign_equity_investment=foreign_equity_investment,
                investment_type_id=InvestmentTypeConstant.fdi.value.id,
                sector_id=SectorConstant.renewable_energy_wind.value.id,
            )

        if not expected_gross_value_added:
            assert not project.gross_value_added
        else:
            assert project.gross_value_added == Decimal(expected_gross_value_added)

    @pytest.mark.parametrize(
        'actual_land_date,expected_financial_year',
        (
            (None, 2029),
            (date(1980, 1, 1), 2019),
            (date(2018, 1, 1), 2019),
            (date(2019, 3, 1), 2019),
            (date(2019, 8, 1), 2019),
            (date(2025, 3, 1), 2024),
            (date(2025, 4, 1), 2025),
            (date(2025, 3, 31), 2024),
            (date(2035, 1, 1), 2034),
            (date(2035, 4, 1), 2035),
        ),
    )
    @freeze_time('2030-01-01 01:00:00')
    def test_get_gva_multiplier_financial_year(self, actual_land_date, expected_financial_year):
        """Test for getting the financial that should be used for a given investment project."""
        investment_project = InvestmentProjectFactory(actual_land_date=actual_land_date)
        gva = GrossValueAddedCalculator(investment_project=investment_project)
        assert gva._get_gva_multiplier_financial_year() == expected_financial_year
