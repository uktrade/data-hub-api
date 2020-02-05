import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.core.utils import reverse_with_query_string


class TestLinkCompanyLink(AdminTestMixin):
    """
    Tests the 'Link Company with D&B' link on the change list.
    """

    def test_link_exists(self):
        """
        Test that the link exists for a user with the change company permission.
        """
        list_route_name = admin_urlname(Company._meta, 'changelist')
        list_url = reverse(list_route_name)

        response = self.client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        assert company_link_url in response.rendered_content

    def test_link_does_not_exist_with_only_view_permission(self):
        """
        Test that the link does not exist for a user with only the view company permission.
        """
        list_route_name = admin_urlname(Company._meta, 'changelist')
        list_url = reverse(list_route_name)

        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        response = client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        assert company_link_url not in response.rendered_content


class TestSelectIDsViewGet(AdminTestMixin):
    """
    Test response for GET requests on the select IDs view.
    """

    def test_returns_200(self):
        """
        Tests that a 200 is returned through a GET to the view.
        """
        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        response = self.client.get(company_link_url)

        assert response.status_code == status.HTTP_200_OK

    def test_permission_required(self):
        """
        Tests that a 403 is returned when a user does not have the necessary permissions.
        """
        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)

        response = client.get(company_link_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSelectIDsViewPost(AdminTestMixin):
    """
    Test response for POST requests on the select IDs view.
    """

    def test_valid_input_redirects_to_confirmation(self):
        """
        Test that valid POST input responds with a redirect to the confirmation
        page.
        """
        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        data = {
            'company': CompanyFactory().id,
            'duns_number': '123456789',
        }
        response = self.client.post(company_link_url, data=data)

        company_link_confirmation_route_name = admin_urlname(
            Company._meta,
            'dnb-link-review-changes',
        )
        company_link_confirmation_url = reverse_with_query_string(
            company_link_confirmation_route_name,
            data,
        )

        assert response.status_code == status.HTTP_302_FOUND
        assert response['location'] == company_link_confirmation_url

    @pytest.mark.parametrize(
        'data_overrides,expected_error',
        (
            (
                # No data
                {
                    'company': '',
                    'duns_number': '',
                },
                'This field is required.',
            ),
            (
                {
                    'company': 'abc123',  # Invalid company ID
                },
                '“abc123” is not a valid UUID.',
            ),
            (
                {
                    'duns_number': '1',  # Invalid duns number
                },
                'Ensure this value has at least 9 characters (it has 1).',
            ),
        ),
    )
    def test_invalid_input_responds_error(self, data_overrides, expected_error):
        """
        Test that some invalid POST input responds with an expected error in rendered content.
        """
        data = {
            'company': CompanyFactory().id,
            'duns_number': '123456789',
            **data_overrides,
        }
        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        response = self.client.post(company_link_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert expected_error in response.rendered_content

    def test_company_already_linked_responds_error(self):
        """
        Test that when a company has already been D&B linked, the view responds with an error.
        """
        data = {
            'company': CompanyFactory(duns_number='999999999').id,
            'duns_number': '123456789',
        }
        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        response = self.client.post(company_link_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        expected_error = 'This company has already been linked with a D&amp;B company.'
        assert expected_error in response.rendered_content

    def test_duns_number_already_linked_responds_error(self):
        """
        Test that when a duns number has already been linked to a Data Hub company, the view
        responds with an error.
        """
        CompanyFactory(duns_number='123456789')
        data = {
            'company': CompanyFactory().id,
            'duns_number': '123456789',
        }
        company_link_route_name = admin_urlname(Company._meta, 'dnb-link-select-ids')
        company_link_url = reverse(company_link_route_name)

        response = self.client.post(company_link_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        expected_error = 'This duns number has already been linked with a Data Hub company.'
        assert expected_error in response.rendered_content
