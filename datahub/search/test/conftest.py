import datetime

from django.conf import settings
from django.core import management
from django.db.models.signals import post_save
from elasticsearch.helpers.test import get_test_client
from pytest import fixture

from datahub.company.models import Company, Contact
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.investment.models import InvestmentProject
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search import elasticsearch
from datahub.search.management.commands import sync_es

from ..company.models import Company as ESCompany
from ..contact.models import Contact as ESContact
from ..investment.models import InvestmentProject as ESInvestmentProject


@fixture(scope='session')
def client(request):
    """Makes the ES test helper client available."""
    from elasticsearch_dsl.connections import connections
    client = get_test_client(nowait=False)
    connections.add_connection('default', client)
    return client


@fixture(scope='session')
def setup_data(client):
    """Sets up the data and makes the ES client available."""
    index = settings.ES_INDEX

    create_test_index(client, index)

    # Create models in the test index
    ESCompany.init(index=index)
    ESContact.init(index=index)
    ESInvestmentProject.init(index=index)

    ContactFactory(first_name='abc', last_name='defg').save()
    ContactFactory(first_name='first', last_name='last').save()
    InvestmentProjectFactory(
        name='abc defg',
        description='investmentproject1',
        estimated_land_date=datetime.datetime(2011, 6, 13, 9, 44, 31, 62870)
    )
    InvestmentProjectFactory(
        description='investmentproject2',
        estimated_land_date=datetime.datetime(2057, 6, 13, 9, 44, 31, 62870),
        project_manager=AdviserFactory(),
        project_assurance_adviser=AdviserFactory(),
    )

    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_uk
    )
    CompanyFactory(
        name='abc defg us ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_us,
        registered_address_country_id=country_us
    )

    management.call_command(sync_es.Command())
    client.indices.refresh()

    yield client
    client.indices.delete(index)


def create_test_index(client, index):
    """Creates/configures the test index."""
    if client.indices.exists(index=index):
        client.indices.delete(index)

    elasticsearch.configure_index(index, {
        'number_of_shards': 1,
        'number_of_replicas': 0,
    })


@fixture
def post_save_handlers():
    """Registeres signals handlers to trigger ES logic."""
    from datahub.search.company.signals import company_sync_es
    from datahub.search.contact.signals import contact_sync_es
    from datahub.search.investment.signals import investment_project_sync_es

    post_save.connect(company_sync_es, sender=Company, dispatch_uid='company_sync_es')
    post_save.connect(contact_sync_es, sender=Contact, dispatch_uid='contact_sync_es')
    post_save.connect(
        investment_project_sync_es,
        sender=InvestmentProject,
        dispatch_uid='investment_project_sync_es'
    )

    yield (company_sync_es, contact_sync_es, investment_project_sync_es,)

    post_save.disconnect(company_sync_es, sender=Company, dispatch_uid='company_sync_es')
    post_save.disconnect(contact_sync_es, sender=Contact, dispatch_uid='contact_sync_es')
    post_save.disconnect(
        investment_project_sync_es,
        sender=InvestmentProject,
        dispatch_uid='investment_project_sync_es'
    )
