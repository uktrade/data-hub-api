from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.messages import get_messages
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.core.utils import reverse_with_query_string


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')


def _get_review_changes_url(company, duns_number):
    review_changes_route_name = admin_urlname(Company._meta, 'dnb-link-review-changes')
    data = {
        'company': company.id,
        'duns_number': duns_number,
    }
    return reverse_with_query_string(
        review_changes_route_name,
        data,
    )


class TestReviewChangesViewGet(AdminTestMixin):
    """
    Test the review changes view with GET requests.
    """

    def test_permission_required(self):
        """
        Test that a user without permission to change companies gets a 403.
        """
        review_changes_url = _get_review_changes_url(CompanyFactory(), '123456789')
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        response = client.get(review_changes_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'data_overrides,expected_error',
        (
            (
                {'company': None, 'duns_number': None},  # No data
                'Company: This field is required. duns_number: This field is required.',
            ),
            (
                {
                    'company': 'abc123',  # Invalid company ID
                },
                'Company: “abc123” is not a valid UUID.',
            ),
            (
                {
                    'duns_number': '1',  # Invalid duns number
                },
                'Duns_number: Ensure this value has at least 9 characters (it has 1).',
            ),
        ),
    )
    def test_validation_errors_rendered(self, data_overrides, expected_error):
        """
        Test that validation errors are rendered as expected.
        """
        review_changes_route_name = admin_urlname(Company._meta, 'dnb-link-review-changes')
        data = {
            'company': CompanyFactory().id,
            'duns_number': '123456789',
            **data_overrides,
        }
        review_changes_url = reverse_with_query_string(
            review_changes_route_name,
            {key: value for key, value in data.items() if value is not None},
        )

        response = self.client.get(review_changes_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert expected_error in response.rendered_content

    def test_dh_company_already_linked_renders_error(self):
        """
        Test that a validation error is rendered if the Data Hub company is already D&B linked.
        """
        review_changes_url = _get_review_changes_url(
            CompanyFactory(duns_number='123456789'),
            '999999999',
        )

        response = self.client.get(review_changes_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        expected_error = 'This company has already been linked with a D&amp;B company.'
        assert expected_error in response.rendered_content

    def test_duns_number_already_linked_renders_error(self):
        """
        Test that a validation error is rendered if the duns number has already been linked to a
        Data Hub company.
        """
        duns_number = '123456789'
        CompanyFactory(duns_number=duns_number)
        review_changes_url = _get_review_changes_url(
            CompanyFactory(),
            duns_number,
        )

        response = self.client.get(review_changes_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        expected_error = 'This duns number has already been linked with a Data Hub company.'
        assert expected_error in response.rendered_content

    def test_changes_returned(self, requests_mock, dnb_response):
        """
        Test that the review changes view renders proposed D&B changes.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response,
        )
        review_changes_url = _get_review_changes_url(
            CompanyFactory(),
            '123456789',
        )
        response = self.client.get(review_changes_url)
        assert response.status_code == status.HTTP_200_OK
        dnb_company = dnb_response['results'][0]
        assert dnb_company['address_line_1'] in response.rendered_content
        assert dnb_company['primary_name'] in response.rendered_content


class TestReviewChangesViewPost(AdminTestMixin):
    """
    Test the review changes view with POST requests.
    """

    def test_post(self, requests_mock, dnb_response):
        """
        Test that a post request to 'review changes' updates the company.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response,
        )
        dh_company = CompanyFactory()
        review_changes_url = _get_review_changes_url(dh_company, '123456789')
        response = self.client.post(review_changes_url)
        assert response.status_code == status.HTTP_302_FOUND

        dh_company.refresh_from_db()
        dnb_company = dnb_response['results'][0]

        assert dh_company.name == dnb_company['primary_name']
        assert dh_company.address_1 == dnb_company['address_line_1']
        assert dh_company.address_2 == dnb_company['address_line_2']
        assert dh_company.address_town == dnb_company['address_town']
        assert dh_company.address_county == dnb_company['address_county']
        assert dh_company.address_country.iso_alpha2_code == dnb_company['address_country']
        assert (
            dh_company.global_ultimate_duns_number
            == dnb_company['global_ultimate_duns_number']
        )


class TestReviewChangesViewDNBErrors(AdminTestMixin):
    """
    Test the review changes view - for both GET and POST - when dnb-service returns errors.
    """

    @pytest.mark.parametrize(
        'http_method',
        ('GET', 'POST'),
    )
    @pytest.mark.parametrize(
        'dnb_response_code',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_dnb_service_error(self, requests_mock, http_method, dnb_response_code):
        """
        Tests that the users get an error message if the dnb-service
        doesn't return with a 200 status code.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=dnb_response_code,
        )
        review_changes_url = _get_review_changes_url(CompanyFactory(), '123456789')
        if http_method == 'GET':
            response = self.client.get(review_changes_url)
        else:
            response = self.client.post(review_changes_url)
        assert response.status_code == status.HTTP_302_FOUND

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert str(messages[0]) == 'Something went wrong in an upstream service.'

    @pytest.mark.parametrize(
        'http_method',
        ('GET', 'POST'),
    )
    @pytest.mark.parametrize(
        'search_results, expected_message',
        (
            (
                [],
                'No matching company found in D&B database.',
            ),
            (
                ['foo', 'bar'],
                'Something went wrong in an upstream service.',
            ),
            (
                [{'duns_number': '012345678'}],
                'Something went wrong in an upstream service.',
            ),
        ),
    )
    def test_dnb_response_invalid(
        self,
        requests_mock,
        http_method,
        search_results,
        expected_message,
    ):
        """
        Test if we get anything other than a single company from dnb-service,
        we return an error message to the user.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
            json={'results': search_results},
        )
        review_changes_url = _get_review_changes_url(CompanyFactory(), '123456789')
        if http_method == 'GET':
            response = self.client.get(review_changes_url)
        else:
            response = self.client.post(review_changes_url)
        assert response.status_code == status.HTTP_302_FOUND

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert str(messages[0]) == expected_message

    def test_post_dnb_data_invalid(
        self,
        requests_mock,
        dnb_response,
    ):
        """
        Tests that if the data returned from DNB does not clear DataHub validation, we show an
        appropriate message to our users.
        """
        dnb_response['results'][0]['primary_name'] = None
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response,
        )
        review_changes_url = _get_review_changes_url(CompanyFactory(), '123456789')
        response = self.client.post(review_changes_url)
        assert response.status_code == status.HTTP_302_FOUND

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert str(messages[0]) == 'Data from D&B did not pass the Data Hub validation checks.'
