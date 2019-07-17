from unittest.mock import Mock

import pytest

from datahub.core.test_utils import random_obj_for_model
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.models import InvestmentBusinessActivity


@pytest.mark.django_db
class TestUpdateGVAOnBusinessActivitiesM2MChanged:
    """
    Tests for the update_gross_value_added_on_project_business_activities_m2m_changed
    signal receiver.
    """

    def test_add(self, monkeypatch):
        """
        Test that the GVA of a project is updated when a business activity is added to the
        project.
        """
        project = InvestmentProjectFactory()

        set_gross_value_added_for_investment_project_mock = Mock()
        monkeypatch.setattr(
            'datahub.investment.project.signals.set_gross_value_added_for_investment_project',
            set_gross_value_added_for_investment_project_mock,
        )

        business_activity = random_obj_for_model(InvestmentBusinessActivity)
        project.business_activities.add(business_activity)

        set_gross_value_added_for_investment_project_mock.assert_called_once_with(project)

    def test_remove(self, monkeypatch):
        """
        Test that the GVA of a project is updated when a business activity is removed from
        the project.
        """
        business_activity = random_obj_for_model(InvestmentBusinessActivity)
        project = InvestmentProjectFactory(business_activities=[business_activity])

        set_gross_value_added_for_investment_project_mock = Mock()
        monkeypatch.setattr(
            'datahub.investment.project.signals.set_gross_value_added_for_investment_project',
            set_gross_value_added_for_investment_project_mock,
        )

        project.business_activities.remove(business_activity)

        set_gross_value_added_for_investment_project_mock.assert_called_once_with(project)

    def test_clear(self, monkeypatch):
        """Test that the GVA of a project is updated when its business activities are cleared."""
        business_activity = random_obj_for_model(InvestmentBusinessActivity)
        project = InvestmentProjectFactory(business_activities=[business_activity])

        set_gross_value_added_for_investment_project_mock = Mock()
        monkeypatch.setattr(
            'datahub.investment.project.signals.set_gross_value_added_for_investment_project',
            set_gross_value_added_for_investment_project_mock,
        )

        project.business_activities.clear()

        set_gross_value_added_for_investment_project_mock.assert_called_once_with(project)
