import uuid
from unittest import mock

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse
from rest_framework import status

from datahub.company.admin.company import CompanyAdmin
from datahub.company.admin_reports import OneListReport
from datahub.company.models import Company
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyCoreTeamMemberFactory,
    CompanyFactory,
)
from datahub.core.test_utils import AdminTestMixin

pytestmark = pytest.mark.django_db


class TestChangeCompanyAdmin(AdminTestMixin):
    """Tests for the company admin change form."""

    def test_add_one_list_core_team_members(self):
        """Test that One List Core Team members can be added to a company."""
        team_member_advisers = AdviserFactory.create_batch(2)
        team_size = len(team_member_advisers)
        company = CompanyFactory()

        assert company.core_team_members.count() == 0

        url = reverse('admin:company_company_change', args=(company.id,))

        data = {}

        # populate data with required field values
        admin_form = CompanyAdmin(Company, site).get_form(mock.Mock())
        for field_name, field in admin_form.base_fields.items():
            if field.required:
                field_value = getattr(company, field_name)
                data[field_name] = field.prepare_value(field_value)

        # add inline related field data
        data.update({
            'core_team_members-TOTAL_FORMS': team_size,
            'core_team_members-INITIAL_FORMS': 0,
            'core_team_members-MIN_NUM_FORMS': 0,
            'core_team_members-MAX_NUM_FORMS': 1000,
        })
        for index, adviser in enumerate(team_member_advisers):
            team_member_id = uuid.uuid4()
            data.update({
                f'initial-core_team_members-{index}-id': team_member_id,
                f'core_team_members-{index}-id': team_member_id,
                f'core_team_members-{index}-company': company.pk,
                f'core_team_members-{index}-adviser': adviser.pk,
            })

        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert company.core_team_members.count() == team_size

    def test_delete_one_list_core_team_members(self):
        """Test that One List Core Team members can be deleted from a company."""
        company = CompanyFactory()
        core_team_members = CompanyCoreTeamMemberFactory.create_batch(2, company=company)
        team_size = len(core_team_members)

        url = reverse('admin:company_company_change', args=(company.id,))

        data = {}

        # populate data with required field values
        admin_form = CompanyAdmin(Company, site).get_form(mock.Mock())
        for field_name, field in admin_form.base_fields.items():
            if field.required:
                field_value = getattr(company, field_name)
                data[field_name] = field.prepare_value(field_value)

        # add inline related field data
        data.update({
            'core_team_members-TOTAL_FORMS': team_size,
            'core_team_members-INITIAL_FORMS': team_size,
            'core_team_members-MIN_NUM_FORMS': 0,
            'core_team_members-MAX_NUM_FORMS': 1000,
        })
        for index, team_member in enumerate(core_team_members):
            data.update({
                f'initial-core_team_members-{index}-id': team_member.pk,
                f'core_team_members-{index}-id': team_member.pk,
                f'core_team_members-{index}-company': company.pk,
                f'core_team_members-{index}-adviser': team_member.adviser.pk,

            })

        # mark first one for deletion
        data['core_team_members-0-DELETE'] = '1'

        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert company.core_team_members.count() == team_size - 1


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
