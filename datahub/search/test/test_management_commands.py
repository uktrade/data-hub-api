import json
from io import StringIO
from unittest import mock

import pytest
from django.core import management


from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search.management.commands import create_alias, delete_alias, get_alias, sync_es

from ..models import DataSet
from ..company.models import Company as ESCompany
from ..contact.models import Contact as ESContact
from ..investment.models import InvestmentProject as ESInvestmentProject

pytestmark = pytest.mark.django_db


def test_batch_rows():
    """Tests _batch_rows."""
    rows = ({}, {}, {})

    res = list(sync_es._batch_rows(rows, batch_size=2))

    assert len(res) == 2
    assert len(res[0]) == 2
    assert len(res[1]) == 1


@mock.patch('datahub.search.management.commands.sync_es.bulk')
@mock.patch('datahub.search.management.commands.sync_es.get_dataset')
def test_sync_dataset(get_dataset, bulk):
    """Tests syncing dataset up to Elasticsearch."""
    get_dataset.return_value = (
        DataSet([CompanyFactory(), CompanyFactory()], ESCompany),
        DataSet([ContactFactory()], ESContact),
        DataSet([InvestmentProjectFactory()], ESInvestmentProject)
    )

    management.call_command(sync_es.Command(), batch_size=1)

    assert bulk.call_count == 4


@mock.patch('datahub.search.management.commands.create_alias.connections.get_connection')
def test_create_alias(get_connection):
    """Tests creating alias for Elasticsearch index."""
    es = get_connection.return_value

    current_index = 'test_index'
    alias_name = 'test_index_alias'

    management.call_command(create_alias.Command(),
                            current_index=current_index,
                            alias_name=alias_name)

    es.indices.put_alias.assert_called_with(
        index=current_index,
        name=alias_name,
    )


@mock.patch('datahub.search.management.commands.delete_alias.connections.get_connection')
def test_delete_alias(get_connection):
    """Tests creating alias for Elasticsearch index."""
    es = get_connection.return_value

    current_index = 'test_index'
    alias_name = 'test_index_alias'

    management.call_command(delete_alias.Command(),
                            current_index=current_index,
                            alias_name=alias_name)

    es.indices.delete_alias.assert_called_with(
        index=current_index,
        name=alias_name,
    )


@mock.patch('datahub.search.management.commands.delete_alias.connections.get_connection')
def test_get_alias(get_connection):
    """Tests creating alias for Elasticsearch index."""
    es = get_connection.return_value

    current_index = 'test_index'

    aliases = {
        'test_index': {
            'aliases': {
                'test_alias': {}
            }
        }
    }

    es.indices.get_alias.return_value = aliases

    out = StringIO()
    management.call_command(get_alias.Command(), current_index=current_index, stdout=out)

    es.indices.get_alias.assert_called_with(
        index=current_index,
    )

    result = json.loads(out.getvalue())

    assert aliases == result
