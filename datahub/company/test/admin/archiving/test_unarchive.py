import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.core.utils import reverse_with_query_string


class TestUnarchiveCompanyLink(AdminTestMixin):
    """
    Tests the 'unarchive' link on the change form.
    """

    def test_link_exists(self):
        """
        Test that the link exists for a user with the change company permission.
        """
        company = ArchivedCompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.pk,))

        response = self.client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        unarchive_route_name = admin_urlname(Company._meta, 'unarchive-company')
        unarchive_query_args = {
            'company': company.pk,
        }
        unarchive_url = reverse_with_query_string(
            unarchive_route_name,
            unarchive_query_args,
        )

        assert unarchive_url in response.rendered_content

    def test_link_does_not_exist_with_only_view_permission(self):
        """
        Test that the link does not exist for a user with only the view company permission.
        """
        company = ArchivedCompanyFactory()

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

        unarchive_route_name = admin_urlname(Company._meta, 'unarchive-company')
        unarchive_url = reverse(unarchive_route_name)

        assert unarchive_url not in response.rendered_content

    def test_link_does_not_exist_company_not_archived(self):
        """
        Test that the link does not exist for a user with only the view company permission.
        """
        company = CompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.pk,))

        response = self.client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        unarchive_route_name = admin_urlname(Company._meta, 'unarchive-company')
        unarchive_url = reverse(unarchive_route_name)

        assert unarchive_url not in response.rendered_content


class TestUnarchiveCompanyViewGet(AdminTestMixin):
    """Tests GET requests for the 'unarchive company' view."""

    @pytest.mark.parametrize(
        'company_callable,expected_status_code',
        (
            # Unarchive of an archived company is successful
            (
                ArchivedCompanyFactory,
                status.HTTP_302_FOUND,
            ),
            # Unarchive of an un-archived company responds with bad request
            (
                CompanyFactory,
                status.HTTP_400_BAD_REQUEST,
            ),
        ),
    )
    def test_unarchive_view(
        self,
        company_callable,
        expected_status_code,
    ):
        """
        Test the unarchive view when called on companies in different states.
        """
        company = company_callable()
        unarchive_route_name = admin_urlname(Company._meta, 'unarchive-company')
        unarchive_query_args = {
            'company': company.pk,
        }
        unarchive_url = reverse_with_query_string(
            unarchive_route_name,
            unarchive_query_args,
        )

        response = self.client.get(unarchive_url)

        assert response.status_code == expected_status_code
        company.refresh_from_db()
        assert company.archived is False
        assert not company.archived_on
        assert not company.archived_by
        assert not company.archived_reason

    def test_unarchive_company_does_not_exist(self):
        """
        Test that a 400 is returned when an invalid value is passed in the query string.

        This could only happen if the query string was manipulated, or the referenced company
        was deleted.
        """
        unarchive_route_name = admin_urlname(Company._meta, 'unarchive-company')
        unarchive_query_args = {
            'company': 'abc123',
        }
        unarchive_url = reverse_with_query_string(
            unarchive_route_name,
            unarchive_query_args,
        )

        response = self.client.get(unarchive_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unarchive_permission_denied(self):
        """
        Test the unarchive view when the user does not have sufficient permissions
        to unarchive a company.
        """
        company = ArchivedCompanyFactory()
        unarchive_route_name = admin_urlname(Company._meta, 'unarchive-company')
        unarchive_query_args = {
            'company': company.pk,
        }
        unarchive_url = reverse_with_query_string(
            unarchive_route_name,
            unarchive_query_args,
        )
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)

        response = client.get(unarchive_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        company.refresh_from_db()
        assert company.archived is True
