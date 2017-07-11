import datetime

from django.conf import settings
from django.core import management
from django.db.models.signals import post_save
from elasticsearch.helpers.test import get_test_client
from pytest import fixture

from datahub.company.models import Company, Contact
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.investment.models import InvestmentProject
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search import models, elasticsearch
from datahub.search.management.commands import sync_es


@fixture(scope='session')
def client(request):
    from elasticsearch_dsl.connections import connections
    client = get_test_client(nowait=False)
    connections.add_connection('default', client)
    return client


@fixture(scope='session')
def setup_data(client):
    index = settings.ES_INDEX

    create_test_index(client, index)

    # Create models in the test index
    models.Company.init(index=index)
    models.Contact.init(index=index)
    models.InvestmentProject.init(index=index)

    ContactFactory(first_name='abc', last_name='defg').save()
    ContactFactory(first_name='first', last_name='last').save()
    InvestmentProjectFactory(
        name='abc defg',
        description='investmentproject1',
        estimated_land_date=datetime.datetime(2011, 6, 13, 9, 44, 31, 62870)
    ).save()
    InvestmentProjectFactory(
        description='investmentproject2',
        estimated_land_date=datetime.datetime(2057, 6, 13, 9, 44, 31, 62870)
    ).save()

    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_uk
    ).save()
    CompanyFactory(
        name='abc defg us ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_us,
        registered_address_country_id=country_us
    ).save()

    management.call_command(sync_es.Command())
    client.indices.refresh()

    yield client
    client.indices.delete(index)


def create_test_index(client, index):
    if client.indices.exists(index=index):
        client.indices.delete(index)

    elasticsearch.configure_index(index, {
        'number_of_shards': 1,
        'number_of_replicas': 0,
    })

@fixture
def post_save_handlers():
    from datahub.search.signals import company_sync_es, contact_sync_es, investment_project_sync_es

    post_save.connect(company_sync_es, sender=Company, dispatch_uid='company_sync_es')
    post_save.connect(contact_sync_es, sender=Contact, dispatch_uid='contact_sync_es')
    post_save.connect(investment_project_sync_es, sender=InvestmentProject, dispatch_uid='investment_project_sync_es')

    yield (company_sync_es, contact_sync_es, investment_project_sync_es,)

    post_save.disconnect(company_sync_es, sender=Company, dispatch_uid='company_sync_es')
    post_save.disconnect(contact_sync_es, sender=Contact, dispatch_uid='contact_sync_es')
    post_save.disconnect(investment_project_sync_es, sender=InvestmentProject,
                         dispatch_uid='investment_project_sync_es')
