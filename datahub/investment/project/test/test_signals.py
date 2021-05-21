from unittest.mock import Mock

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import (
    Country as CountryConstant,
    InvestmentProjectStage as InvestmentProjectStageConstant,
)
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


@pytest.mark.django_db
class TestInvestorCompanyUpdate:
    """
    Tests for the update_country_investment_originates_from_post_save signal receiver.
    """

    def test_update_investor_company_updates_country_of_origin_for_in_progress_project(self):
        """
        Test that in progress investment projects' country investment originates from field
        is updated when corresponding investor company address country is updated.
        """
        investor_company = CompanyFactory(
            address_country_id=CountryConstant.japan.value.id,
        )
        projects = InvestmentProjectFactory.create_batch(
            2,
            investor_company=investor_company,
            stage_id=InvestmentProjectStageConstant.prospect.value.id,
        )

        for project in projects:
            assert (
                str(project.country_investment_originates_from_id)
                == CountryConstant.japan.value.id
            )

        investor_company.address_country_id = CountryConstant.united_states.value.id
        investor_company.save()

        for project in projects:
            project.refresh_from_db()
            assert (
                str(project.country_investment_originates_from_id)
                == CountryConstant.united_states.value.id
            )

    def test_update_investor_company_doesnt_update_country_of_origin_for_won_project(self):
        """
        Test that won investment projects' country investment originates from field
        is not updated when corresponding investor company address country is updated.
        """
        investor_company = CompanyFactory(
            address_country_id=CountryConstant.japan.value.id,
        )
        projects = InvestmentProjectFactory.create_batch(
            2,
            investor_company=investor_company,
            stage_id=InvestmentProjectStageConstant.won.value.id,
        )

        for project in projects:
            assert (
                str(project.country_investment_originates_from_id)
                == CountryConstant.japan.value.id
            )

        investor_company.address_country_id = CountryConstant.united_states.value.id
        investor_company.save()

        for project in projects:
            project.refresh_from_db()
            assert (
                str(project.country_investment_originates_from_id)
                == CountryConstant.japan.value.id
            )
