import uuid
from unittest import mock

import pytest
from django.contrib.admin.sites import site
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.test import Client
from django.urls import reverse
from rest_framework import status

from datahub.company.admin.company import CompanyAdmin, MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.company.admin_reports import OneListReport
from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyCoreTeamMemberFactory,
    CompanyFactory,
)
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.feature_flag.test.factories import FeatureFlagFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def merge_list_feature_flag():
    """Creates the merge tool feature flag."""
    yield FeatureFlagFactory(code=MERGE_COMPANY_TOOL_FEATURE_FLAG)


class TestChangeCompanyAdmin(AdminTestMixin):
    """Tests for the company admin change form."""

    def test_add_core_team_members(self):
        """Test that core team members can be added to a company."""
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

    def test_delete_core_team_members(self):
        """Test that core team members can be deleted from a company."""
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


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestMergeWithAnotherCompanyLink(AdminTestMixin):
    """Tests the 'merge with another company' link on the change form."""

    def test_link_exists(self):
        """Test that the link exists for a user with the change company permission."""
        company = CompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.pk,))

        response = self.client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name, args=(company.pk,))

        assert select_other_url in response.rendered_content

    def test_link_does_not_exist_with_only_view_permission(self):
        """Test that the link does not exist for a user with only the view company permission."""
        company = CompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.pk,))

        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        response = client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name, args=(company.pk,))

        assert select_other_url not in response.rendered_content


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestMergeWithAnotherCompanyView(AdminTestMixin):
    """Tests the 'merge with another company' form."""

    SAME_COMPANY = object()

    def test_proceeds_if_valid_company_provided(self):
        """Test the view redirects if a valid company is provided."""
        main_company = CompanyFactory()
        other_company = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name, args=(main_company.pk,))

        response = self.client.get(
            select_other_url,
            follow=True,
            data={
                'other_company': str(other_company.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        changelist_route_name = admin_urlname(Company._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        assert response.redirect_chain[0][0] == changelist_url

    @pytest.mark.parametrize(
        'other_company,expected_error',
        (
            (
                SAME_COMPANY,
                'The two companies to merge cannot be the same. Please select a different '
                'company.',
            ),
            (
                '1234',
                "'1234' is not a valid UUID.",
            ),
            (
                '',
                'This field is required.',
            ),
        ),
    )
    def test_error_if_same_company_provided(self, other_company, expected_error):
        """
        Test that an error is displayed if the same company is provided as the second
        company.
        """
        company = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name, args=(company.pk,))

        value = str(company.pk) if other_company is self.SAME_COMPANY else other_company

        response = self.client.get(
            select_other_url,
            data={
                'other_company': value,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']

        assert 'other_company' in form.errors
        assert form.errors['other_company'] == [expected_error]


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


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestCompanyAdminPermissions(AdminTestMixin):
    """Test permission handling in various views."""

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                True,
                'get',
            ),
        ),
    )
    def test_redirects_to_login_page_if_not_logged_in(self, route_name, needs_arg, method):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        args = (CompanyFactory().pk,) if needs_arg else ()
        url = reverse(route_name, args=args)

        client = Client()
        request_func = getattr(client, method)
        response = request_func(url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                True,
                'get',
            ),
        ),
    )
    def test_redirects_to_login_page_if_not_staff(self, route_name, needs_arg, method):
        """Test that the view redirects to the login page if the user isn't a member of staff."""
        args = (CompanyFactory().pk,) if needs_arg else ()
        url = reverse(route_name, args=args)

        user = create_test_user(is_staff=False, password=self.PASSWORD)
        client = self.create_client(user=user)
        request_func = getattr(client, method)

        response = request_func(url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                True,
                'get',
            ),
        ),
    )
    def test_permission_denied_if_staff_and_without_change_permission(
            self,
            route_name,
            needs_arg,
            method,
    ):
        """
        Test that the view returns a 403 response if the staff user does not have the
        change company permission.
        """
        args = (CompanyFactory().pk,) if needs_arg else ()
        url = reverse(route_name, args=args)

        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        request_func = getattr(client, method)

        response = request_func(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
