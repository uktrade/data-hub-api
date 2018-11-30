import uuid
from unittest import mock

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse
from rest_framework import status

from datahub.company.admin.company import CompanyAdmin
from datahub.company.admin_reports import OneListReport
from datahub.company.models import Company, OneListTier
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    OneListCoreTeamMemberFactory,
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

        assert company.one_list_core_team_members.count() == 0

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
            'one_list_core_team_members-TOTAL_FORMS': team_size,
            'one_list_core_team_members-INITIAL_FORMS': 0,
            'one_list_core_team_members-MIN_NUM_FORMS': 0,
            'one_list_core_team_members-MAX_NUM_FORMS': 1000,
        })
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

    def test_delete_one_list_core_team_members(self):
        """Test that One List Core Team members can be deleted from a company."""
        company = CompanyFactory()
        core_team_members = OneListCoreTeamMemberFactory.create_batch(2, company=company)
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
            'one_list_core_team_members-TOTAL_FORMS': team_size,
            'one_list_core_team_members-INITIAL_FORMS': team_size,
            'one_list_core_team_members-MIN_NUM_FORMS': 0,
            'one_list_core_team_members-MAX_NUM_FORMS': 1000,
        })
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

    @pytest.mark.parametrize(
        'get_test_tier_ids',
        (
            lambda available_tiers: ('', available_tiers[1]),
            lambda available_tiers: (available_tiers[0], ''),
            lambda available_tiers: (available_tiers[0], available_tiers[1]),
        ),
    )
    def test_classification_mirrors_one_list_tier(self, get_test_tier_ids):
        """
        Test that classification mirrors one_list_tier when a company is saved.
        """
        tiers_ids = OneListTier.objects.values_list('id', flat=True)[:2]
        initial_tier_id, new_tier_id = get_test_tier_ids(tiers_ids)

        company = CompanyFactory(
            one_list_tier_id=initial_tier_id,
            classification_id=initial_tier_id,
        )

        url = reverse('admin:company_company_change', args=(company.id,))

        data = {
            'one_list_core_team_members-TOTAL_FORMS': 0,
            'one_list_core_team_members-INITIAL_FORMS': 0,
            'one_list_core_team_members-MIN_NUM_FORMS': 0,
            'one_list_core_team_members-MAX_NUM_FORMS': 1000,
        }

        # populate data with required field values
        admin_form = CompanyAdmin(Company, site).get_form(mock.Mock())
        for field_name, field in admin_form.base_fields.items():
            if field.required:
                field_value = getattr(company, field_name)
                data[field_name] = field.prepare_value(field_value)

        data['one_list_tier'] = new_tier_id

        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        company.refresh_from_db()
        if not new_tier_id:
            assert not company.classification
        else:
            assert company.classification_id == new_tier_id


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
