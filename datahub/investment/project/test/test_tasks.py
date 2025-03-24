from decimal import Decimal
from unittest import mock

import pytest

from datahub.core.constants import Sector as SectorConstant
from datahub.investment.project.constants import FDISICGrouping as FDISICGroupingConstant
from datahub.investment.project.models import GVAMultiplier
from datahub.investment.project.tasks import (
    _update_investment_projects_for_gva_multiplier,
    update_investment_projects_for_gva_multiplier_task,
)
from datahub.investment.project.test.factories import (
    FDIInvestmentProjectFactory,
    GVAMultiplierFactory,
)

CAPITAL = GVAMultiplier.SectorClassificationChoices.CAPITAL
LABOUR = GVAMultiplier.SectorClassificationChoices.LABOUR

pytestmark = pytest.mark.django_db


class TestInvestmentProjectTasks:
    """Test investment projects tasks."""

    @mock.patch(
        'datahub.investment.project.tasks._update_investment_projects_for_gva_multiplier',
    )
    def test_update_investment_projects_for_gva_multiplier_task_when_multiplier_does_not_exist(
        self,
        mock_update_investment_projects_for_gva_multiplier,
        caplog,
    ):
        """Tests update investment projects for gva multiplier task when
        a GVA Multiplier no longer exists.
        """
        caplog.set_level('WARNING')

        update_investment_projects_for_gva_multiplier_task(1234)

        assert len(caplog.messages) == 1
        assert caplog.messages[0] == (
            'Unable to find GVA Multiplier [1234] - '
            'Unable to update associated investment projects'
        )
        assert not mock_update_investment_projects_for_gva_multiplier.called

    @mock.patch(
        'datahub.investment.project.tasks._update_investment_projects_for_gva_multiplier',
    )
    def test_update_investment_projects_for_gva_multiplier_task(
        self,
        mock_update_investment_projects_for_gva_multiplier,
    ):
        """Tests update investment projects for gva multiplier task updates
        calls update_investment_projects_for_gva.
        """
        gva_multipler = GVAMultiplierFactory()
        mock_update_investment_projects_for_gva_multiplier.return_value = None
        update_investment_projects_for_gva_multiplier_task(gva_multipler.pk)
        assert mock_update_investment_projects_for_gva_multiplier.called

    def test_update_investment_projects_for_gva_multiplier(self):
        """Tests update investment projects for gva multiplier task updates
        all related investment projects.
        """
        gva_multiplier = GVAMultiplierFactory(
            multiplier=Decimal('1'),
            financial_year=3010,
            sector_id=SectorConstant.renewable_energy_wind.value.id,
            sector_classification_gva_multiplier=CAPITAL,
            sector_classification_value_band=CAPITAL,
            fdi_sic_grouping_id=FDISICGroupingConstant.electric.value.id,
        )

        with mock.patch(
            'datahub.investment.project.gva_utils.GrossValueAddedCalculator._get_gva_multiplier',
        ) as mock_get_multiplier:
            mock_get_multiplier.return_value = gva_multiplier
            fdi_project = FDIInvestmentProjectFactory(
                foreign_equity_investment=10000,
            )

            fdi_project_2 = FDIInvestmentProjectFactory(
                foreign_equity_investment=20000,
            )

            assert fdi_project.gross_value_added == 10000
            assert fdi_project_2.gross_value_added == 20000

            assert fdi_project.modified_on
            modified_on = fdi_project.modified_on

            gva_multiplier.multiplier = 2
            _update_investment_projects_for_gva_multiplier(gva_multiplier)

            fdi_project.refresh_from_db()
            fdi_project_2.refresh_from_db()

            assert fdi_project.gross_value_added == 20000
            assert fdi_project.modified_on == modified_on

            assert fdi_project_2.gross_value_added == 40000
