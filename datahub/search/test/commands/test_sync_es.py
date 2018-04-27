from unittest import mock

import pytest
from django.core import management

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search.management.commands import sync_es
from ...apps import get_search_apps
from ...company.models import Company as ESCompany
from ...contact.models import Contact as ESContact
from ...investment.models import InvestmentProject as ESInvestmentProject
from ...models import DataSet

pytestmark = pytest.mark.django_db


@mock.patch('datahub.search.bulk_sync.bulk')
@mock.patch('datahub.search.management.commands.sync_es.get_datasets')
def test_sync_dataset(get_datasets, bulk, setup_es):
    """Tests syncing dataset up to Elasticsearch."""
    get_datasets.return_value = (
        DataSet([CompanyFactory(), CompanyFactory()], ESCompany),
        DataSet([ContactFactory()], ESContact),
        DataSet([InvestmentProjectFactory()], ESInvestmentProject)
    )

    management.call_command(sync_es.Command(), batch_size=1)

    assert bulk.call_count == 4


@pytest.mark.parametrize(
    'search_model',
    (app.name for app in get_search_apps())
)
@mock.patch('datahub.search.bulk_sync.bulk')
def test_sync_one_model(bulk, setup_es, search_model):
    """
    Test that --model can be used to specify what we weant to sync.
    """
    management.call_command(sync_es.Command(), model=[search_model])

    assert bulk.call_count == 1


@mock.patch('datahub.search.bulk_sync.bulk')
def test_sync_all_models(bulk, setup_es):
    """
    Test that if --model is not used, all the search apps are synced.
    """
    management.call_command(sync_es.Command())

    assert bulk.call_count == len(get_search_apps())


@mock.patch('datahub.search.bulk_sync.bulk')
def test_sync_invalid_model(bulk, setup_es):
    """
    Test that if an invalid value is used with --model, nothing gets synced.
    """
    management.call_command(sync_es.Command(), model='invalid')

    assert bulk.call_count == 0
