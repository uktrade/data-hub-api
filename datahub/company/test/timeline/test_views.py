from unittest.mock import Mock
from urllib.parse import urljoin

import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user


class TestCompanyTimelineViews(APITestMixin):
    """Tests for the company timeline view."""

    def test_list(self, requests_mock, response_signature):
        """Test the retrieval of the timeline for a company."""
        stubbed_url = urljoin(
            settings.DATA_SCIENCE_COMPANY_API_URL,
            '/api/v1/company/events/?companies_house_id=125694',
        )
        stubbed_response_data = {
            'events': [
                {
                    'data_source': 'companies_house.companies',
                    'data_source_label': 'Companies House (Companies)',
                    'datetime': 'Mon, 31 Dec 2018 00:00:00 GMT',
                    'description': 'Accounts next due date',
                },
                {
                    'data_source': 'dit.export_wins',
                    'data_source_label': 'DIT (Export Wins)',
                    'datetime': 'Mon, 31 Dec 2017 00:00:00 GMT',
                    'description': 'Export Win',
                },
            ],
        }

        requests_mock.get(
            stubbed_url,
            json=stubbed_response_data,
            headers=response_signature,
        )

        company = CompanyFactory(company_number='0125694')
        url = reverse('api-v4:company:timeline-collection', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'data_source': 'companies_house.companies',
                    'data_source_label': 'Companies House (Companies)',
                    'datetime': '2018-12-31T00:00:00Z',
                    'description': 'Accounts next due date',
                },
                {
                    'data_source': 'dit.export_wins',
                    'data_source_label': 'DIT (Export Wins)',
                    'datetime': '2017-12-31T00:00:00Z',
                    'description': 'Export Win',
                },
            ],
        }

    def test_list_with_no_matching_company_in_reporting_service(self, requests_mock):
        """
        Test the retrieval of the timeline for a company with no matching record in the
        upstream service.
        """
        stubbed_url = urljoin(
            settings.DATA_SCIENCE_COMPANY_API_URL,
            '/api/v1/company/events/?companies_house_id=125694',
        )
        requests_mock.get(stubbed_url, status_code=status.HTTP_404_NOT_FOUND)

        company = CompanyFactory(company_number='0125694')
        url = reverse('api-v4:company:timeline-collection', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    @pytest.mark.parametrize('company_number', (None, '', '00'))
    def test_list_with_no_company_number(self, company_number):
        """Test the retrieval of the timeline for a company without a valid company number."""
        company = CompanyFactory(company_number=company_number)
        url = reverse('api-v4:company:timeline-collection', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    @pytest.mark.parametrize(
        'status_code',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_list_with_error_from_upstream_server(
            self,
            monkeypatch,
            requests_mock,
            status_code,
    ):
        """Test the behaviour when an error is returned from the upstream service."""
        error_reference = 'error-ref-1'
        monkeypatch.setattr(
            'sentry_sdk.capture_exception',
            Mock(return_value=error_reference),
        )
        stubbed_url = urljoin(
            settings.DATA_SCIENCE_COMPANY_API_URL,
            '/api/v1/company/events/?companies_house_id=125694',
        )
        requests_mock.get(stubbed_url, status_code=status_code)

        company = CompanyFactory(company_number='125694')
        url = reverse('api-v4:company:timeline-collection', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = response.json()

        assert response_data == {
            'detail': f'Error communicating with the company timeline API. Error reference: '
                      f'{error_reference}.',
        }

    def test_list_with_invalid_upstream_response(
            self,
            monkeypatch,
            requests_mock,
            response_signature,
    ):
        """
        Test the behaviour when an data is returned in an unexpected format from the
        upstream service.
        """
        error_reference = 'error-ref-1'
        monkeypatch.setattr(
            'sentry_sdk.capture_exception',
            Mock(return_value=error_reference),
        )

        stubbed_url = urljoin(
            settings.DATA_SCIENCE_COMPANY_API_URL,
            '/api/v1/company/events/?companies_house_id=1000',
        )
        stubbed_response_data = {
            'events': [
                {
                    'data_source_wrong': 'companies_house.companies',
                    'data_source_label_wrong': 'Companies House (Companies)',
                    'datetime_wrong': 'Mon, 31 Dec 2018 00:00:00 GMT',
                    'description_wrong': 'Accounts next due date',
                },
                {
                    'data_source_wrong': 'dit.export_wins',
                    'data_source_label_wrong': 'DIT (Export Wins)',
                    'datetime_wrong': 'Mon, 31 Dec 2017 00:00:00 GMT',
                    'description_wrong': 'Export Win',
                },
            ],
        }

        requests_mock.get(stubbed_url, json=stubbed_response_data, headers=response_signature)

        company = CompanyFactory(company_number='1000')
        url = reverse('api-v4:company:timeline-collection', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = response.json()

        assert response_data == {
            'detail': f'Unexpected response data format received from the company timeline API. '
                      f'Error reference: {error_reference}.',
        }

    @pytest.mark.parametrize(
        'permission_codenames',
        (
            (CompanyPermission.view_company,),
            (CompanyPermission.view_company_timeline,),
            (),
        ),
    )
    def test_permission_is_denied(self, permission_codenames):
        """Test that a 403 is returned for users without the correct permissions."""
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:timeline-collection', kwargs={'pk': company.pk})

        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
