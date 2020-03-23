from decimal import Decimal
from unittest import mock

import pytest

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
    Sector as SectorConstant,
)
from datahub.investment.project.management.commands import refresh_gross_value_added_values
from datahub.investment.project.test.factories import InvestmentProjectFactory


pytestmark = pytest.mark.django_db


class TestRefreshGrossValueAddedCommand:
    """Test refreshing gross value added values command."""

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities,multiplier_value,foreign_equity_investment,'
        'gross_value_added',
        (
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [],
                None,
                None,
                None,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                ],
                '0.0581',
                1000,
                '58',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.sales.value.id,
                ],
                '0.0581',
                1000,
                '58',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [InvestmentBusinessActivityConstant.retail.value.id],
                '0.0581',
                1000,
                '58',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                '0.0325',
                1000,
                '33',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.aerospace_assembly_aircraft.value.id,
                [],
                '0.0621',
                1000,
                '62',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                '0.0581',
                1000,
                '58',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                '0.0581',
                None,
                None,
            ),
            (
                InvestmentTypeConstant.commitment_to_invest.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                None,
                1000,
                None,
            ),
            (
                InvestmentTypeConstant.non_fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                ],
                None,
                1000,
                None,
            ),
        ),
    )
    def test_refresh_gross_value_added(
        self,
        investment_type,
        sector,
        business_activities,
        multiplier_value,
        foreign_equity_investment,
        gross_value_added,
    ):
        """Test populating Gross value added data."""
        with mock.patch(
            'datahub.investment.project.signals.set_gross_value_added_for_investment_project',
        ) as mock_update_gva:
            mock_update_gva.return_value = None
            project = InvestmentProjectFactory(
                sector_id=sector,
                business_activities=business_activities,
                investment_type_id=investment_type,
                foreign_equity_investment=foreign_equity_investment,
            )

        assert not project.gva_multiplier
        self._run_command()
        project.refresh_from_db()
        if not multiplier_value:
            assert not project.gva_multiplier
        else:
            assert project.gva_multiplier.multiplier == Decimal(multiplier_value)

        if not gross_value_added:
            assert not project.gross_value_added
        else:
            assert project.gross_value_added == Decimal(gross_value_added)

    def _run_command(self):
        cmd = refresh_gross_value_added_values.Command()
        cmd.handle()
