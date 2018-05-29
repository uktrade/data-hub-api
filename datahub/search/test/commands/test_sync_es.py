from unittest import mock

import pytest
from django.core import management
from django.core.management.base import CommandError

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.test_utils import MockQuerySet
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search.management.commands import sync_es
from ...apps import get_search_apps
from ...company.models import Company as ESCompany
from ...contact.models import Contact as ESContact
from ...investment.models import InvestmentProject as ESInvestmentProject


@mock.patch(
    'datahub.search.management.commands.sync_es.index_exists',
    mock.Mock(return_value=False)
)
def test_fails_if_index_doesnt_exist():
    """Tests that if the index doesn't exist, sync_es fails."""
    with pytest.raises(CommandError):
        management.call_command(sync_es.Command())


@mock.patch('datahub.search.bulk_sync.bulk')
@mock.patch('datahub.search.management.commands.sync_es.get_search_apps_by_name')
@mock.patch(
    'datahub.search.management.commands.sync_es.index_exists',
    mock.Mock(return_value=True)
)
@pytest.mark.django_db
def test_sync_es(get_search_apps_by_name, bulk):
    """Tests syncing app to Elasticsearch."""
    get_search_apps_by_name.return_value = (
        mock.Mock(queryset=MockQuerySet([CompanyFactory(), CompanyFactory()]), es_model=ESCompany),
        mock.Mock(queryset=MockQuerySet([ContactFactory()]), es_model=ESContact),
        mock.Mock(
            queryset=MockQuerySet([InvestmentProjectFactory()]),
            es_model=ESInvestmentProject,
        )
    )

    management.call_command(sync_es.Command(), batch_size=1)

    assert bulk.call_count == 4


@pytest.mark.parametrize(
    'search_model',
    (app.name for app in get_search_apps())
)
@mock.patch('datahub.search.management.commands.sync_es.sync_app')
@mock.patch(
    'datahub.search.management.commands.sync_es.index_exists',
    mock.Mock(return_value=True)
)
def test_sync_one_model(sync_app_mock, search_model):
    """
    Test that --model can be used to specify what we weant to sync.
    """
    management.call_command(sync_es.Command(), model=[search_model])

    assert sync_app_mock.call_count == 1


@mock.patch('datahub.search.management.commands.sync_es.sync_app')
@mock.patch(
    'datahub.search.management.commands.sync_es.index_exists',
    mock.Mock(return_value=True)
)
def test_sync_all_models(sync_app_mock):
    """
    Test that if --model is not used, all the search apps are synced.
    """
    management.call_command(sync_es.Command())

    assert sync_app_mock.call_count == len(get_search_apps())


@mock.patch('datahub.search.management.commands.sync_es.sync_app')
@mock.patch(
    'datahub.search.management.commands.sync_es.index_exists',
    mock.Mock(return_value=True)
)
def test_sync_invalid_model(sync_app_mock):
    """
    Test that if an invalid value is used with --model, nothing gets synced.
    """
    management.call_command(sync_es.Command(), model='invalid')

    assert sync_app_mock.call_count == 0
