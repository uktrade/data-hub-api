import datetime
from unittest import mock

import pytest
from elasticsearch_dsl.connections import connections
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
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
        assert response.data['count'] == 2
        assert response.data['companies'][0]['name'].startswith(term)
        assert [{'count': 2, 'entity': 'company'},
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
        assert [{'count': 2, 'entity': 'company'},
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
        assert [{'count': 2, 'entity': 'company'},
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
        assert response.data['count'] == 2
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

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_contact_by_country_case_insensitive(self):
        """Tests detailed contact search."""
        ContactFactory(
            first_name='John',
            last_name='Doe',
            address_same_as_company=False,
            address_1='Happy Lane',
            address_town='Happy Town',
            address_country_id=constants.Country.united_states.value.id,
        )

        connections.get_connection().indices.refresh()

        term = 'united states'

        url = reverse('api-v3:search:basic')

        response = self.api_client.get(url, {
            'term': term,
            'entity': 'contact',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['contacts']) == 1
        assert response.data['contacts'][0]['address_country']['name'] == 'United States'

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
            'original_query': 'abc defg',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'abc defg'

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
        CompanyFactory(name='The Risk Advisory Group')
        CompanyFactory(name='The Advisory Group')
        CompanyFactory(name='The Advisory')
        CompanyFactory(name='The Advisories')

        connections.get_connection().indices.refresh()

        term = 'The Advisory'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # results are in order of relevance if sortby is not applied
        assert [
            'The Advisory',
            'The Advisory Group',
            'The Risk Advisory Group',
            'The Advisories'
        ] == [company['name'] for company in response.data['companies']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_partial_match(self):
        """Tests partial matching."""
        CompanyFactory(name='Veryuniquename1')
        CompanyFactory(name='Veryuniquename2')
        CompanyFactory(name='Veryuniquename3')
        CompanyFactory(name='Veryuniquename4')

        connections.get_connection().indices.refresh()

        term = 'Veryuniquenam'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # particular order is not important here, we just need all that partially match
        assert {
            'Veryuniquename1',
            'Veryuniquename2',
            'Veryuniquename3',
            'Veryuniquename4'
        } == {company['name'] for company in response.data['companies']}

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_hyphen_match(self):
        """Tests hyphen query."""
        CompanyFactory(name='t-shirt')
        CompanyFactory(name='tshirt')
        CompanyFactory(name='electronic shirt')
        CompanyFactory(name='t and e and a')

        connections.get_connection().indices.refresh()

        term = 't-shirt'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # order of relevance
        assert [
            't-shirt',
            'tshirt',
            'electronic shirt',
            't and e and a'
        ] == [company['name'] for company in response.data['companies']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_id_match(self):
        """Tests exact id matching."""
        CompanyFactory(id='0fb3379c-341c-4dc4-b125-bf8d47b26baa')
        CompanyFactory(id='0fb2379c-341c-4dc4-b225-bf8d47b26baa')
        CompanyFactory(id='0fb4379c-341c-4dc4-b325-bf8d47b26baa')
        CompanyFactory(id='0fb5379c-341c-4dc4-b425-bf8d47b26baa')

        connections.get_connection().indices.refresh()

        term = '0fb4379c-341c-4dc4-b325-bf8d47b26baa'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert '0fb4379c-341c-4dc4-b325-bf8d47b26baa' == response.data['companies'][0]['id']

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_desc(self):
        """Tests sorting in descending order."""
        CompanyFactory(name='Water 1')
        CompanyFactory(name='water 2')
        CompanyFactory(name='water 3')
        CompanyFactory(name='Water 4')

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
    def test_search_contact_sort_by_last_name_desc(self):
        """Tests sorting in descending order."""
        ContactFactory(first_name='test_name', last_name='abcdef')
        ContactFactory(first_name='test_name', last_name='bcdefg')
        ContactFactory(first_name='test_name', last_name='cdefgh')
        ContactFactory(first_name='test_name', last_name='defghi')

        connections.get_connection().indices.refresh()

        term = 'test_name'

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'last_name:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['defghi',
                'cdefgh',
                'bcdefg',
                'abcdef'] == [contact['last_name'] for contact in response.data['results']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_asc(self):
        """Tests sorting in ascending order."""
        CompanyFactory(name='Fire 4')
        CompanyFactory(name='fire 3')
        CompanyFactory(name='fire 2')
        CompanyFactory(name='Fire 1')

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
    def test_search_sort_nested_desc(self):
        """Tests sorting by nested field."""
        InvestmentProjectFactory(
            name='Potato 1',
            stage_id=constants.InvestmentProjectStage.active.value.id,
        )
        InvestmentProjectFactory(
            name='Potato 2',
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )
        InvestmentProjectFactory(
            name='potato 3',
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )
        InvestmentProjectFactory(
            name='Potato 4',
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )

        connections.get_connection().indices.refresh()

        term = 'Potato'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'stage.name:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['Won',
                'Won',
                'Prospect',
                'Active'] == [investment_project['stage']['name']
                              for investment_project in response.data['results']]

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_sort_invalid(self):
        """Tests attempt to sort by non existent field."""
        CompanyFactory(name='Fire 4')
        CompanyFactory(name='fire 3')
        CompanyFactory(name='fire 2')
        CompanyFactory(name='Fire 1')

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
        """Tests placement of null values in sorted results when order is ascending."""
        InvestmentProjectFactory(name='Earth 1', total_investment=1000)
        InvestmentProjectFactory(name='Earth 2')

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
        """Tests placement of null values in sorted results when order is descending."""
        InvestmentProjectFactory(name='Ether 1', total_investment=1000)
        InvestmentProjectFactory(name='Ether 2')

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
        """Tests multiple filters in investment project search.

        We make sure that out of provided investment projects, we will
        receive only those that match our filter.

        We are testing following filter:

        investment_type = fdi
        AND (investor_company = compA OR investor_company = compB)
        AND (stage = won OR stage = active)
        """
        url = reverse('api-v3:search:investment_project')

        investment_project1 = InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.active.value.id
        )
        investment_project2 = InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )

        InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.won.value.id
        )
        InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )

        connections.get_connection().indices.refresh()

        response = self.api_client.post(url, {
            'investment_type': constants.InvestmentType.fdi.value.id,
            'investor_company': [
                investment_project1.investor_company.pk,
                investment_project2.investor_company.pk,
            ],
            'stage': [
                constants.InvestmentProjectStage.won.value.id,
                constants.InvestmentProjectStage.active.value.id,
            ],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

        # checks if we only have investment projects with stages we filtered
        assert {
            constants.InvestmentProjectStage.active.value.id,
            constants.InvestmentProjectStage.won.value.id
        } == {
            investment_project['stage']['id']
            for investment_project in response.data['results']
        }

        # checks if we only have investment projects with investor companies we filtered
        assert {
            str(investment_project1.investor_company.pk),
            str(investment_project2.investor_company.pk)
        } == {
            investment_project['investor_company']['id']
            for investment_project in response.data['results']
        }

        # checks if we only have investment projects with fdi investment type
        assert {
            constants.InvestmentType.fdi.value.id
        } == {
            investment_project['investment_type']['id']
            for investment_project in response.data['results']
        }

    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_investment_project_aggregates(self):
        """Tests aggregates in investment project search."""
        url = reverse('api-v3:search:investment_project')

        InvestmentProjectFactory(
            name='Pear 1',
            stage_id=constants.InvestmentProjectStage.active.value.id
        )
        InvestmentProjectFactory(
            name='Pear 2',
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )
        InvestmentProjectFactory(
            name='Pear 3',
            stage_id=constants.InvestmentProjectStage.prospect.value.id
        )
        InvestmentProjectFactory(
            name='Pear 4',
            stage_id=constants.InvestmentProjectStage.won.value.id
        )

        connections.get_connection().indices.refresh()

        response = self.api_client.post(url, {
            'original_query': 'Pear',
            'stage': [
                constants.InvestmentProjectStage.prospect.value.id,
                constants.InvestmentProjectStage.active.value.id,
            ],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3
        assert 'aggregations' in response.data

        stages = [{'key': constants.InvestmentProjectStage.prospect.value.id, 'doc_count': 2},
                  {'key': constants.InvestmentProjectStage.active.value.id, 'doc_count': 1},
                  {'key': constants.InvestmentProjectStage.won.value.id, 'doc_count': 1}]
        assert all(stage in response.data['aggregations']['stage'] for stage in stages)
