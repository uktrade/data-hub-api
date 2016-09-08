from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.urlresolvers import reverse
from api.management.commands.load_ch import Command as Loadch
from api.models.company import Company

from datahubapi import settings


class CompanyTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def setup_db_and_index(self):
        load_ch = Loadch()
        load_ch.handle(filename='test.csv')

    # When you save a company, and you include the company number
    # companies house is the source of truth for that stuff, so
    # What happens is the frontend sends bare details and we fill in a few from the CH entry

    def test_post_company_adds_to_db(self):
        self.setup_db_and_index()

        test_data = dict(
            company_number='06768809',
            region='North-West',
            sectors='Tech'
        )

        print("URL")
        print(reverse('company-list'))
        print("=========================")

        response = self.client.post(reverse('company-list'), test_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'API Response tells the client the object was created')

        self.assertIsNotNone(response.data['id'],
                             'Confirm that a new ID was returned for the created object')

        # Test that if we save a company and insert CH data into it
        # for those people not using datahub and still on old CDMS
        company = Company.objects.get(pk=response.data['id'])
        self.assertEqual(company.registered_name, 'CORPORATE UMBRELLA LIMITED')
        self.assertEqual(company.company_number, '06768809')
        self.assertEqual(company.business_type, 'Private Limited Company')
        self.assertEqual(company.region, 'North-West')
        self.assertEqual(company.sectors, 'Tech')

    def test_post_company_updates_existing_ch_index_record(self):
        self.setup_db_and_index()

        test_data = dict(
            company_number='06768809',
            region='North-West',
            sectors='Tech',
            trading_name='Freds'
        )

        response = self.client.post(reverse('company-list'), test_data, format='json')

        query = {
            "query": {
                "query_string": {"query": test_data["company_number"]},
            },
        }

        es_results = settings.ES_CLIENT.search(index='datahub', body=query)

        self.assertEqual(es_results['hits']['total'], 1)

        hit = es_results['hits']['hits'][0]['_source']

        self.assertEqual(hit['result_type'], 'COMBINED')
        self.assertEqual(hit['source_id'], response.data['id'])
        self.assertEqual(hit['company_number'], '06768809')
        self.assertEqual(hit['title'], 'CORPORATE UMBRELLA LIMITED')
        self.assertEqual(hit['alt_title'], 'Freds')
