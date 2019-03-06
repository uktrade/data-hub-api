from unittest import mock

import pytest
from reversion.models import Version

from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.models import FeatureFlag
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.investment.project.constants import FEATURE_FLAG_STREAMLINED_FLOW
from datahub.investment.project.management.commands import activate_streamlined_investment_flow
from datahub.investment.project.test.factories import (
    AssignPMInvestmentProjectFactory,
    VerifyWinInvestmentProjectFactory,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def set_streamlined_flow_feature_flag_as_inactive():
    """Creates the streamlined flow feature flag."""
    yield FeatureFlagFactory(
        code=FEATURE_FLAG_STREAMLINED_FLOW,
        is_active=False,
        description='description of feature',
    )


class TestActivateStreamlinedInvestmentFlowCommand:
    """Tests for activate streamlined investment flow command."""

    def _check_activate_streamlined_investment_flow_feature(self):
        command = activate_streamlined_investment_flow.Command()
        command.activate_streamlined_investment_flow_feature()

        feature = FeatureFlag.objects.get(code=FEATURE_FLAG_STREAMLINED_FLOW)

        assert feature.is_active
        assert feature.description == activate_streamlined_investment_flow.FEATURE_DESCRIPTION

    def test_activate_streamlined_investment_flow_feature_when_feature_does_not_exist(self):
        """Test creating and activating the investment flow feature flag."""
        self._check_activate_streamlined_investment_flow_feature()

    @pytest.mark.usefixtures('set_streamlined_flow_feature_flag_as_inactive')
    def test_activate_streamlined_investment_flow_feature_when_feature_does_exist(self):
        """Test updating and activating the investment flow feature flag."""
        self._check_activate_streamlined_investment_flow_feature()

    def test_move_assign_pm_investment_projects_back_to_prospect(self):
        """
        Test moving any existing project that is at the assign pm stage back
        to a prospect and check an audit entry has been logged.
        """
        assign_pm_project = AssignPMInvestmentProjectFactory()
        verify_win_project = VerifyWinInvestmentProjectFactory()

        command = activate_streamlined_investment_flow.Command()
        command.move_assign_pm_investment_projects_back_to_prospect()

        assign_pm_project.refresh_from_db()
        verify_win_project.refresh_from_db()

        assert str(assign_pm_project.stage.id) == InvestmentProjectStage.prospect.value.id
        assert str(verify_win_project.stage.id) == InvestmentProjectStage.verify_win.value.id
        assert Version.objects.get_for_object(assign_pm_project).count() == 1
        assert Version.objects.get_for_object(verify_win_project).count() == 0

    @mock.patch('datahub.investment.project.management.commands.'
                'activate_streamlined_investment_flow.Command.'
                'move_assign_pm_investment_projects_back_to_prospect')
    @mock.patch('datahub.investment.project.management.commands.'
                'activate_streamlined_investment_flow.Command.'
                'activate_streamlined_investment_flow_feature')
    def test_command_handle_calls_all_methods(self, mock_activate, mock_move_projects):
        """Test all methods are called when the command handle is called."""
        mock_activate.return_value = None
        mock_move_projects.return_value = None

        command = activate_streamlined_investment_flow.Command()
        command.handle()

        mock_activate.assert_called_once()
        mock_move_projects.assert_called_once()
