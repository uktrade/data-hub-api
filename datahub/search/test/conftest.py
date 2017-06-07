from django.conf import settings
from django.core import management
from elasticsearch.helpers.test import get_test_client
from elasticsearch_dsl import Index
from pytest import fixture

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.search import models
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

    ContactFactory(first_name='abc', last_name='defg').save()
    ContactFactory(first_name='first', last_name='last').save()

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

    index = Index(index)
    index.create()
