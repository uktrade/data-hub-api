import uuid
from unittest import mock

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse
from rest_framework import status

from datahub.company.admin.company import CompanyAdmin, CompanyAdminForm
from datahub.company.admin_reports import OneListReport
from datahub.company.models import Company
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.core.test_utils import AdminTestMixin

pytestmark = pytest.mark.django_db


def get_required_company_form_data(company=None):
    """
    :returns: dict with all required fields to use in tests when posting
    to an add/edit admin company url.
    """
    if not company:
        company = CompanyFactory.build()

    data = {
        'export_segment': '',
        'export_sub_segment': '',
        'one_list_core_team_members-TOTAL_FORMS': 0,
        'one_list_core_team_members-INITIAL_FORMS': 0,
        'one_list_core_team_members-MIN_NUM_FORMS': 0,
        'one_list_core_team_members-MAX_NUM_FORMS': 1000,
    }
    admin_form = CompanyAdmin(Company, site).get_form(mock.Mock())
    for field_name, field in admin_form.base_fields.items():
        if field.required:
            field_value = getattr(company, field_name)
            data[field_name] = field.prepare_value(field_value)
    return data


class TestTradingNamesInCompanyAdmin(AdminTestMixin):
    """Tests for the trading_names array field in the admin."""

    def test_default_size_with_new_company(self):
        """
        Test that when adding a new company, the default size for the trading names
        form field is shown and used.
        """
        default_size = CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE

        url = reverse('admin:company_company_add')

        # check that the add company form has the right size for trading names
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        form_field = response.context['adminform'].form.fields['trading_names']
        assert form_field.size == default_size

        # check that posting data for all form fields related to trading names
        # saves the model correctly
        trading_names_data = {
            f'trading_names_{i}': f'trading name {i}'
            for i in range(default_size)
        }

        data = {
            **get_required_company_form_data(),
            **trading_names_data,
        }

        response = self.client.post(url, data=data, follow=True)
        assert response.status_code == status.HTTP_200_OK
        assert Company.objects.count() == 1
        assert Company.objects.first().trading_names == list(trading_names_data.values())

    @pytest.mark.parametrize(
        'trading_names_number,expected_field_size',
        (
            (
                0,
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE,
            ),
            (
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE - 1,
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE,
            ),
            (
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE,
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE + 1,
            ),
            (
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE + 1,
                CompanyAdminForm.TRADING_NAMES_DEFAULT_FIELD_SIZE + 2,
            ),
        ),
    )
    def test_right_field_size_with_existing_company(
        self,
        trading_names_number,
        expected_field_size,
    ):
        """
        Test that when editing an existing company, the correct size for the trading_names
        form field is set.
        """
        company = CompanyFactory(
            trading_names=[
                f'trading name {i}'
                for i in range(trading_names_number)
            ],
        )
        url = reverse('admin:company_company_change', args=(company.id,))

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        form_field = response.context['adminform'].form.fields['trading_names']
        assert form_field.size == expected_field_size


class TestOneListMembersInCompanyAdmin(AdminTestMixin):
    """Tests for the one list members in the admin."""

    def test_add(self):
        """Test that One List Core Team members can be added to a company."""
        team_member_advisers = AdviserFactory.create_batch(2)
        team_size = len(team_member_advisers)
        company = CompanyFactory()

        assert company.one_list_core_team_members.count() == 0

        url = reverse('admin:company_company_change', args=(company.id,))

        data = {
            **get_required_company_form_data(company),

            'one_list_core_team_members-TOTAL_FORMS': team_size,
            'one_list_core_team_members-INITIAL_FORMS': 0,
            'one_list_core_team_members-MIN_NUM_FORMS': 0,
            'one_list_core_team_members-MAX_NUM_FORMS': 1000,
        }

        for index, adviser in enumerate(team_member_advisers):
            team_member_id = uuid.uuid4()
            data.update({
                f'initial-one_list_core_team_members-{index}-id': team_member_id,
                f'one_list_core_team_members-{index}-id': team_member_id,
                f'one_list_core_team_members-{index}-company': company.pk,
                f'one_list_core_team_members-{index}-adviser': adviser.pk,
            })

        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert company.one_list_core_team_members.count() == team_size

    def test_delete(self):
        """Test that One List Core Team members can be deleted from a company."""
        company = CompanyFactory()
        core_team_members = OneListCoreTeamMemberFactory.create_batch(2, company=company)
        team_size = len(core_team_members)

        url = reverse('admin:company_company_change', args=(company.id,))

        data = {
            **get_required_company_form_data(company),

            'one_list_core_team_members-TOTAL_FORMS': team_size,
            'one_list_core_team_members-INITIAL_FORMS': team_size,
            'one_list_core_team_members-MIN_NUM_FORMS': 0,
            'one_list_core_team_members-MAX_NUM_FORMS': 1000,
        }

        for index, team_member in enumerate(core_team_members):
            data.update({
                f'initial-one_list_core_team_members-{index}-id': team_member.pk,
                f'one_list_core_team_members-{index}-id': team_member.pk,
                f'one_list_core_team_members-{index}-company': company.pk,
                f'one_list_core_team_members-{index}-adviser': team_member.adviser.pk,

            })

        # mark first one for deletion
        data['one_list_core_team_members-0-DELETE'] = '1'

        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert company.one_list_core_team_members.count() == team_size - 1


class TestOneListLink(AdminTestMixin):
    """
    Tests for the one list export.
    """

    def test_one_list_link_exists(self):
        """
        Test that there is a link to export the one list on the company change list.
        """
        url = reverse('admin:company_company_changelist')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        one_list_url = reverse(
            'admin-report:download-report',
            kwargs={'report_id': OneListReport.id},
        )
        assert one_list_url in response.rendered_content
