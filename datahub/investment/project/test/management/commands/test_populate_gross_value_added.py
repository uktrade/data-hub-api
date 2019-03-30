from unittest import mock

import pytest

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
    Sector as SectorConstant,
)
from datahub.investment.project.management.commands import populate_gross_value_added
from datahub.investment.project.test.factories import InvestmentProjectFactory


pytestmark = pytest.mark.django_db


class TestPopulateGrossValueAddedCommand:
    """Test populate gross value added command."""

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities,multiplier_value',
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
                0.0581,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [InvestmentBusinessActivityConstant.retail.value.id],
                0.0581,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                0.0325,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.aerospace_assembly_aircraft.value.id,
                [],
                0.0621,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                0.0581,
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
    def test_populate_gross_value_added(
        self,
        investment_type,
        sector,
        business_activities,
        multiplier_value,
    ):
        """Test populating Gross value added data."""
        with mock.patch(
            'datahub.investment.project.signals.update_gross_value_added_for_investment_project',
        ) as mock_update_gva:
            mock_update_gva.return_value = None
            project = InvestmentProjectFactory(
                sector_id=sector,
                business_activities=business_activities,
                investment_type_id=investment_type,
                foreign_equity_investment=1000,
            )

        assert not project.gva_multiplier
        self._run_populate_command()
        project.refresh_from_db()
        if not multiplier_value:
            assert project.gva_multiplier is None
        else:
            assert project.gva_multiplier.multiplier == multiplier_value

    def _run_populate_command(self):
        cmd = populate_gross_value_added.Command()
        cmd.handle()
