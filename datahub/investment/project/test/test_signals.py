from unittest.mock import Mock

import pytest
import reversion
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import (
    Country as CountryConstant,
)
from datahub.core.constants import (
    InvestmentProjectStage as InvestmentProjectStageConstant,
)

# from core.models import Country
from datahub.core.test_utils import random_obj_for_model
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.models import InvestmentBusinessActivity


@pytest.mark.django_db
class TestUpdateGVAOnBusinessActivitiesM2MChanged:
    """Tests for the update_gross_value_added_on_project_business_activities_m2m_changed
    signal receiver.
    """

    def test_add(self, monkeypatch):
        """Test that the GVA of a project is updated when a business activity is added to the
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
        """Test that the GVA of a project is updated when a business activity is removed from
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
    """Tests for the update_country_investment_originates_from_post_save signal receiver.
    """

    def test_update_investor_company_updates_country_of_origin_for_in_progress_project(self):
        """Test that in progress investment projects' country investment originates from field
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
        """Test that won investment projects' country investment originates from field
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


@pytest.mark.django_db
class TestUpdateProjectSiteAddressFieldsWhenCompanyAddressChanges:

    def test_update_project_site_address_fields_when_company_address_changes(self):
        """Test post save signal updates site address in applicable investment projects."""
        old_address_fields = {
            'address_1': 'Old Admiralty Building',
            'address_2': 'Whitehall',
            'address_town': 'London',
            'address_postcode': 'SW1A 2AA',
        }
        # setup models
        with reversion.create_revision():
            uk_based_company = CompanyFactory(
                address_country_id=CountryConstant.united_kingdom.value.id,
                **old_address_fields,
            )
            project_to_update = InvestmentProjectFactory(
                uk_company=uk_based_company,
                site_address_is_company_address=True,
                **old_address_fields,
            )
            project_to_not_update = InvestmentProjectFactory(
                uk_company=uk_based_company,
                site_address_is_company_address=False,
                **old_address_fields,
            )

        # initial assertions
        assert Version.objects.get_for_object(project_to_update).count() == 1
        assert Version.objects.get_for_object(project_to_not_update).count() == 1

        # update company address
        new_address_fields = {
            'address_1': '10 Downing Street',
            'address_2': 'Whitehall',
            'address_town': 'Manchester',
            'address_postcode': 'M1 1AA',
        }
        for attribute, value in new_address_fields.items():
            setattr(uk_based_company, attribute, value)
        uk_based_company.save()

        # final assertions
        project_to_update.refresh_from_db()
        assert project_to_update.site_address_is_company_address is True
        assert project_to_update.address_1 == new_address_fields['address_1']
        assert project_to_update.address_2 == new_address_fields['address_2']
        assert project_to_update.address_town == new_address_fields['address_town']
        assert project_to_update.address_postcode == new_address_fields['address_postcode']
        assert Version.objects.get_for_object(project_to_update).count() == 2

        project_to_not_update.refresh_from_db()
        assert project_to_not_update.site_address_is_company_address is False
        assert project_to_not_update.address_1 == old_address_fields['address_1']
        assert project_to_not_update.address_2 == old_address_fields['address_2']
        assert project_to_not_update.address_town == old_address_fields['address_town']
        assert project_to_not_update.address_postcode == old_address_fields['address_postcode']
        assert Version.objects.get_for_object(project_to_not_update).count() == 1
