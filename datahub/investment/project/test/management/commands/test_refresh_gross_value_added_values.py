import logging
from decimal import Decimal
from unittest import mock

import pytest

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
    Sector as SectorConstant,
)
from datahub.investment.project.management.commands import refresh_gross_value_added_values
from datahub.investment.project.tasks import (
    refresh_gross_value_added_value_for_fdi_investment_projects,
)
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
)

pytestmark = pytest.mark.django_db


class TestRefreshGrossValueAddedCommand:
    """Test refreshing gross value added values command."""

    @pytest.mark.parametrize(
        'investment_type,sector,business_activities,multiplier_value,'
        'foreign_equity_investment,number_new_jobs,gross_value_added',
        (
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [],
                None,
                None,
                None,
                None,
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                ],
                '51983.514030000',
                1000,
                200,
                '10396703',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                None,
                [
                    InvestmentBusinessActivityConstant.sales.value.id,
                ],
                '51983.514030000',
                1000,
                200,
                '10396703',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [InvestmentBusinessActivityConstant.retail.value.id],
                '51983.514030000',
                1000,
                200,
                '10396703',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                '0.093757195',
                1000,
                200,
                '94',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.aerospace_assembly_aircraft.value.id,
                [],
                '0.209650945',
                1000,
                200,
                '210',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                '51983.514030000',
                1000,
                200,
                '10396703',
            ),
            (
                InvestmentTypeConstant.fdi.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [
                    InvestmentBusinessActivityConstant.retail.value.id,
                    InvestmentBusinessActivityConstant.other.value.id,
                ],
                '51983.514030000',
                None,
                200,
                '10396703',
            ),
            (
                InvestmentTypeConstant.commitment_to_invest.value.id,
                SectorConstant.renewable_energy_wind.value.id,
                [],
                None,
                1000,
                200,
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
                200,
                None,
            ),
        ),
    )
    def test_refresh_gross_value_added(
        self,
        caplog,
        investment_type,
        sector,
        business_activities,
        multiplier_value: str | None,
        foreign_equity_investment,
        number_new_jobs,
        gross_value_added: str | None,
    ):
        """Test populating Gross value added data."""
        caplog.set_level(logging.INFO)

        with mock.patch(
            'datahub.investment.project.signals.set_gross_value_added_for_investment_project',
        ) as mock_update_gva:
            mock_update_gva.return_value = None
            project = InvestmentProjectFactory(
                sector_id=sector,
                business_activities=business_activities,
                investment_type_id=investment_type,
                foreign_equity_investment=foreign_equity_investment,
                number_new_jobs=number_new_jobs,
            )

        assert project.gva_multiplier is None
        refresh_gross_value_added_value_for_fdi_investment_projects()
        project.refresh_from_db()
        if multiplier_value is None:
            assert project.gva_multiplier is None
        else:
            assert project.gva_multiplier.multiplier == Decimal(multiplier_value)

        if gross_value_added is None:
            assert project.gross_value_added is None
        else:
            assert project.gross_value_added == Decimal(gross_value_added)

        assert any(
            'Task refresh_gross_value_added_value_for_fdi_investment_projects completed'
            in message for message in caplog.messages
        )

    def test_schedule_refresh_gross_value_added_value_for_fdi_investment_projects(
        self,
        caplog,
        monkeypatch,
    ):
        """Tests that refresh gross value added value for fdi investment projects is scheduled."""
        caplog.set_level(logging.INFO)
        self._run_command()

        assert any(
            'schedule_refresh_gross_value_added_value_for_fdi_investment_projects'
            in message for message in caplog.messages
        )

    def _run_command(self):
        cmd = refresh_gross_value_added_values.Command()
        cmd.handle()
