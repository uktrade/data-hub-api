import datetime
from unittest import mock

import pytest
from elasticsearch_dsl.connections import connections
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import (
    APITestMixin, synchronous_executor_submit, synchronous_transaction_on_commit,
)
from datahub.investment.test.factories import InvestmentProjectFactory


pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures('setup_data', 'post_save_handlers')
class TestSearch(APITestMixin):
    """Tests search views."""

    def test_basic_search_all_companies(self):
        """Tests basic aggregate all companies query."""
        term = ''

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0

    def test_basic_search_companies(self):
        """Tests basic aggregate companies query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert response.data['companies'][0]['name'].startswith(term)
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'},
                {'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_basic_search_contacts(self):
        """Tests basic aggregate contacts query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'contact'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['contacts'][0]['first_name'] in term
        assert response.data['contacts'][0]['last_name'] in term
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'},
                {'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_basic_search_investment_projects(self):
        """Tests basic aggregate investment project query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['investment_projects'][0]['name'] == term
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'},
                {'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_basic_search_companies_no_results(self):
        """Tests case where there should be no results."""
        term = 'there-should-be-no-match'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.data['count'] == 0

    def test_basic_search_companies_no_term(self):
        """Tests case where there is not term provided."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_basic_search_companies_invalid_entity(self):
        """Tests case where provided entity is invalid."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': 'test',
            'entity': 'sloths',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_basic_search_paging(self):
        """Tests pagination of results."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company',
            'offset': 1,
            'limit': 1,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['companies']) == 1

    def test_search_company(self):
        """Tests detailed company search."""
        term = 'abc defg'

        url = reverse('api-v3:search:company')
        united_states_id = constants.Country.united_states.value.id

        response = self.api_client.post(url, {
            'original_query': term,
            'trading_address_country': united_states_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['trading_address_country']['id'] == united_states_id

    def test_search_company_no_filters(self):
        """Tests case where there is no filters provided."""
        url = f"{reverse('api-v3:search:company')}"
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_foreign_company_json(self):
        """Tests detailed company search."""
        url = reverse('api-v3:search:company')

        response = self.api_client.post(url, {
            'uk_based': False,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['uk_based'] is False

    def test_search_contact(self):
        """Tests detailed contact search."""
        term = 'abc defg'

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'original_query': term,
            'last_name': 'defg',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['last_name'] == 'defg'

    def test_search_contact_no_filters(self):
        """Tests case where there is no filters provided."""
        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_investment_project_json(self):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'description': 'investmentproject1',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['description'] == 'investmentproject1'

    def test_search_investment_project_date_json(self):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'estimated_land_date_before': datetime.datetime(2017, 6, 13, 9, 44, 31, 62870),
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1

    def test_search_investment_project_invalid_date_json(self):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'estimated_land_date_before': 'this is definitely not a valid date',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_investment_project_no_filters(self):
        """Tests case where there is no filters provided."""
        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_results_quality(self):
        """Tests quality of results."""
        CompanyFactory(name='The Risk Advisory Group').save()
        CompanyFactory(name='The Advisory Group').save()
        CompanyFactory(name='The Advisory').save()
        CompanyFactory(name='The Advisories').save()

        connections.get_connection().indices.refresh()

        term = 'The Advisory'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['The Advisory',
                'The Advisory Group',
                'The Risk Advisory Group',
                'The Advisories'] == [company['name'] for company in response.data['companies']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_desc(self):
        """Tests quality of results."""
        CompanyFactory(name='Water 1').save()
        CompanyFactory(name='water 2').save()
        CompanyFactory(name='water 3').save()
        CompanyFactory(name='Water 4').save()

        connections.get_connection().indices.refresh()

        term = 'Water'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'sortby': 'name:desc',
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['Water 4',
                'water 3',
                'water 2',
                'Water 1'] == [company['name'] for company in response.data['companies']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_asc(self):
        """Tests quality of results."""
        CompanyFactory(name='Fire 4').save()
        CompanyFactory(name='fire 3').save()
        CompanyFactory(name='fire 2').save()
        CompanyFactory(name='Fire 1').save()

        connections.get_connection().indices.refresh()

        term = 'Fire'

        url = reverse('api-v3:search:company')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'name:asc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['Fire 1',
                'fire 2',
                'fire 3',
                'Fire 4'] == [company['name'] for company in response.data['results']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_invalid(self):
        """Tests quality of results."""
        CompanyFactory(name='Fire 4').save()
        CompanyFactory(name='fire 3').save()
        CompanyFactory(name='fire 2').save()
        CompanyFactory(name='Fire 1').save()

        connections.get_connection().indices.refresh()

        term = 'Fire'

        url = reverse('api-v3:search:company')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'some_field_that_doesnt_exist:asc'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_asc_with_null_values(self):
        """Tests quality of results."""
        InvestmentProjectFactory(name='Earth 1', total_investment=1000).save()
        InvestmentProjectFactory(name='Earth 2').save()

        connections.get_connection().indices.refresh()

        term = 'Earth'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'total_investment:asc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [('Earth 2', None),
                ('Earth 1', 1000)] == [(investment['name'], investment['total_investment'],)
                                       for investment in response.data['results']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_desc_with_null_values(self):
        """Tests quality of results."""
        InvestmentProjectFactory(name='Ether 1', total_investment=1000).save()
        InvestmentProjectFactory(name='Ether 2').save()

        connections.get_connection().indices.refresh()

        term = 'Ether'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'total_investment:desc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [('Ether 1', 1000),
                ('Ether 2', None)] == [(investment['name'], investment['total_investment'],)
                                       for investment in response.data['results']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_investment_project_multiple_filters(self):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        company_a = CompanyFactory(
            name='companyA'
        )
        company_b = CompanyFactory(
            name='companyB'
        )

        InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            investor_company=company_a,
            sector_id=constants.Sector.aerospace_assembly_aircraft.value.id,
            stage_id=constants.InvestmentProjectStage.active.value.id
        ).save()
        InvestmentProjectFactory(
            investor_company=company_b,
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        ).save()
        InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.won.value.id
        ).save()

        connections.get_connection().indices.refresh()

        response = self.api_client.post(url, {
            'investment_type': constants.InvestmentType.fdi.value.id,
            'investor_company': [
                company_a.pk,
                company_b.pk,
            ],
            'stage': [
                constants.InvestmentProjectStage.won.value.id,
                constants.InvestmentProjectStage.active.value.id,
            ],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1

        stages = set([investment_project['stage']['id']
                      for investment_project in response.data['results']])

        assert constants.InvestmentProjectStage.active.value.id in stages
        assert constants.InvestmentProjectStage.prospect.value.id not in stages
        assert constants.InvestmentProjectStage.won.value.id not in stages
