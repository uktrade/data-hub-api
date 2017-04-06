from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (CompaniesHouseCompanyFactory, CompanyFactory, ContactFactory)
from datahub.core.test_utils import LeelooTestCase
from datahub.interaction.test.factories import InteractionFactory


class SearchViewTestCase(LeelooTestCase):
    """Search test case."""

    def test_search_missing_required_parameter(self):
        """Required parameter missing."""
        url = reverse('search')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == ['Parameter "term" is mandatory.']

    def test_search_by_term(self):
        """Search by term."""
        url = reverse('search')
        response = self.api_client.post(
            url,
            {'term': 'Foo'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_search_term_with_multiple_doc_type_filters(self):
        """Multiple doc type filters."""
        InteractionFactory()
        CompanyFactory(name='Foo')
        ContactFactory(first_name='Foo')
        CompaniesHouseCompanyFactory()

        url = reverse('search')
        expected_types = {'company_company', 'company_contact'}
        response = self.api_client.post(
            url,
            {'term': 'Foo', 'doc_type': expected_types},
            format='json'
        )
        returned_types = set([hit['_type'] for hit in response.data['hits']])

        assert response.status_code == status.HTTP_200_OK
        assert returned_types == expected_types

    def test_search_term_with_single_doc_type_filter(self):
        """Single doc type filter."""
        InteractionFactory()
        CompanyFactory()
        ContactFactory()
        CompaniesHouseCompanyFactory()

        url = reverse('search')
        expected_types = {'company_company'}
        response = self.api_client.post(
            url,
            {'term': 'Foo', 'doc_type': expected_types},
            format='json'
        )
        returned_types = set([hit['_type'] for hit in response.data['hits']])

        assert response.status_code == status.HTTP_200_OK
        assert returned_types == expected_types
