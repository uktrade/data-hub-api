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
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import SectorFactory


CAPITAL = GVAMultiplier.SectorClassificationChoices.CAPITAL
LABOUR = GVAMultiplier.SectorClassificationChoices.LABOUR
DEFAULT_MULTIPLIER = Decimal('0.5')
DEFAULT_NUMBER_NEW_JOBS = 200
DEFAULT_FOREIGN_EQUITY_INVESTMENT = 1000

pytestmark = pytest.mark.django_db


class TestGrossValueAddedCalculator:
    """Test for Gross Value Added Calculator."""

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities',
        [
            # Non-FDI investment type
            (
                InvestmentTypeConstant.non_fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
            ),
            # When sector is empty
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [],
            ),
        ],
    )
    def test_get_gva_multiplier_returns_none_when_expected(
        self,
        investment_type,
        sector,
        business_activities,
    ):
        """Test _get_gva_multiplier_for_investment_project returns none when:
        a) investment type is non-FDI,
        b) investment project sector is empty.
        """
        project = InvestmentProjectFactory(
            sector_id=sector,
            business_activities=business_activities,
            investment_type_id=investment_type,
        )
        assert project.gva_multiplier is None

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities,expected_multiplier_value',
        [
            #  FDI investment project with retail business activity
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                ],
                Decimal('51983.514030000'),
            ),
            #  FDI investment project with sales business activity
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.sales.value.id,
                ],
                Decimal('51983.514030000'),
            ),
            #  FDI investment project with sector and no business activities
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                Decimal('0.093757195'),
            ),
            #  FDI investment project with sector and no business activities
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.aerospace_assembly_aircraft.value.id,
                [],
                Decimal('0.209650945'),
            ),
            #  FDI investment project with sector and retail business activities
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                Decimal('51983.514030000'),
            ),
        ],
    )
    def test_get_gva_multiplier_returns_value_when_expected(
        self,
        investment_type,
        sector,
        business_activities,
        expected_multiplier_value: Decimal,
    ):
        """Test _get_gva_multiplier_for_investment_project returns value when:
        a) investment type is FDI,
        b) business activities are retail or sales,
        c) investment project has a sector.
        """
        project = InvestmentProjectFactory(
            sector_id=sector,
            business_activities=business_activities,
            investment_type_id=investment_type,
        )
        assert project.gva_multiplier.multiplier == expected_multiplier_value

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
            foreign_equity_investment=DEFAULT_FOREIGN_EQUITY_INVESTMENT,
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
            foreign_equity_investment=DEFAULT_FOREIGN_EQUITY_INVESTMENT,
            actual_land_date=date(2050, 5, 1),

        )
        assert project.gva_multiplier is None
        assert caplog.messages[0] == (
            f'Unable to find GVA multiplier for sector {sector.id}'
        )

    def test_no_investment_project_sector_returns_none(self):
        """
        Tests when an investment project has no sector that the GVA multiplier returned is none.
        """
        project = InvestmentProjectFactory(
            business_activities=[],
            investment_type_id=InvestmentTypeConstant.fdi.value.id,
            sector_id=None,
        )
        assert project.gva_multiplier is None

    @pytest.mark.parametrize(
        'sector_classification, foreign_equity_investment, number_new_jobs',
        [
            (
                CAPITAL,
                None,  # No foreign equity investment
                DEFAULT_NUMBER_NEW_JOBS,
            ),
            (
                CAPITAL,
                None,  # No foreign equity investment
                None,  # No number of new jobs
            ),
            (
                LABOUR,
                DEFAULT_FOREIGN_EQUITY_INVESTMENT,
                None,  # No number of new jobs
            ),
            (
                LABOUR,
                None,  # No foreign equity investment
                None,  # No number of new jobs
            ),
        ],
    )
    def test_gva_calculation_based_on_sector_classification_when_expected_gva_is_none(
        self,
        sector_classification,
        foreign_equity_investment,
        number_new_jobs,
    ):
        """
        Tests that GVA value is set to None when:
        a) sector is capital intensive, there is no foreign equity investment value,
        and there is a value for number of new jobs;
        b) sector is capital intensive, there is no foreign equity investment value,
        and there is no value for number of new jobs;
        c) sector is labour intensive, there is a foreign equity investment value,
        and there is no value for number of new jobs;
        d) sector is labour intensive, there is no foreign equity investment value,
        and there is no value for number of new jobs;
        """
        sector = SectorFactory()
        GVAMultiplierFactory(
            multiplier=DEFAULT_MULTIPLIER,
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
        assert project.gross_value_added is None

    @pytest.mark.parametrize(
        'sector_classification, foreign_equity_investment, number_new_jobs, expected_gva_value',
        [
            (
                CAPITAL,
                DEFAULT_FOREIGN_EQUITY_INVESTMENT,
                None,  # No number of new jobs
                Decimal(DEFAULT_MULTIPLIER * DEFAULT_FOREIGN_EQUITY_INVESTMENT),
            ),
            (
                LABOUR,
                None,  # No foreign equity investment
                DEFAULT_NUMBER_NEW_JOBS,
                Decimal(DEFAULT_MULTIPLIER * DEFAULT_NUMBER_NEW_JOBS),
            ),
        ],
    )
    def test_gva_calculation_based_on_sector_classification_when_expected_gva_is_not_none(
        self,
        sector_classification,
        foreign_equity_investment,
        number_new_jobs,
        expected_gva_value: Decimal,
    ):
        """
        Tests that the correct gva value is set when:
        a) Sector classification is capital, there is foreign equity investment,
        and there is no value for number of new jobs
        b) Sector classification is labour, there is no foreign equity investment,
        value and there is a value for number of new jobs
        """
        sector = SectorFactory()
        GVAMultiplierFactory(
            multiplier=DEFAULT_MULTIPLIER,
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
        assert project.gross_value_added == expected_gva_value

    def test_no_gva_multiplier_returns_none(self):
        """
        Tests if a project's GVA multiplier is none, that it returns a GVA value of none.
        """
        project = InvestmentProjectFactory()
        project.gva_multiplier = None
        assert project.gross_value_added is None

    @pytest.mark.parametrize(
        'sector_classification, multiplier_value, foreign_equity_investment, number_new_jobs',
        [
            (CAPITAL, Decimal('0.5'), None, 200),  # Capital intensive, no FEI
            (LABOUR, Decimal('0.5'), 1200, None),  # Labour intensive, no jobs
            (CAPITAL, None, 100000, 50),  # Capital intensive, no GVA multiplier
            (LABOUR, None, 130000000, 1000),  # Labour intensive, no GVA multiplier
            ('another', Decimal('0.5'), 1200, 200),  # Neither labour or capital intensive
        ],
    )
    def test_calculate_gva_when_expected_gva_value_is_none(
        self,
        sector_classification,
        multiplier_value: Decimal | None,
        foreign_equity_investment,
        number_new_jobs,
    ):
        """
        Test various scenarios for correct GVA calculation when gva value is expected to be none
        """
        sector = SectorFactory()
        if multiplier_value is None:
            # avoids violating GVAMultiplier's not-null constraint
            gva_multiplier = None
        else:
            gva_multiplier = GVAMultiplierFactory(
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
            calculated_gva_value = GrossValueAddedCalculator(project).gross_value_added
            assert calculated_gva_value is None

    @pytest.mark.parametrize(
        'sector_classification, multiplier_value, foreign_equity_investment, number_new_jobs, expected_gva_value',  # noqa
        [
            (CAPITAL, Decimal('0.5'), 1200, 200, 600),  # Capital intensive
            (LABOUR, Decimal('0.5'), 1200, 200, 100),   # Labour intensive
            # Capital intensive, large investment
            (CAPITAL, Decimal('0.07'), 5000000, 100, 350000),
            # Labour intensive, moderate number of jobs
            (LABOUR, Decimal('0.15'), 2000000, 500, 75),
            (CAPITAL, Decimal('0.1'), 0, 100, 0),  # Capital intensive, zero investment
            (LABOUR, Decimal('0.05'), 1000000, 0, 0),  # Labour intensive, zero jobs
            # Capital intensive, very large investment
            (CAPITAL, Decimal('1.0'), 999999999999991, 1000, 999999999999991),
            # Labour intensive, minimal jobs; expected value is 0 due to rounding
            (LABOUR, Decimal('0.25'), 150000, 1, 0),
        ],
    )
    def test_calculate_gva_when_expected_gva_value_is_not_none(
        self,
        sector_classification,
        multiplier_value,
        foreign_equity_investment,
        number_new_jobs,
        expected_gva_value: Decimal | None,
    ):
        """
        Test various scenarios for correct calculation when GVA value is expected not to be none.
        """
        sector = SectorFactory()
        if multiplier_value is None:
            # avoids violating GVAMultiplier's not-null constraint
            gva_multiplier = None
        else:
            gva_multiplier = GVAMultiplierFactory(
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
            calculated_gva_value = GrossValueAddedCalculator(project).gross_value_added
            assert calculated_gva_value == expected_gva_value

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
            gva_multiplier.sector_id for gva_multiplier in GVAMultiplier.objects.all()
        ]
        assert set(sector_ids) == set(gva_multiplier_sector_ids)
