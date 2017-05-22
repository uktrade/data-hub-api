from unittest import mock

import pytest
from django.conf import settings
from django.core import management

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.search.management.commands import sync_es

pytestmark = pytest.mark.django_db


def test_id_name_dict():
    """Tests _id_name_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.name = 'test'

    res = sync_es._id_name_dict(obj)

    assert res == {
        'id': str(obj.id),
        'name': obj.name,
    }


def test_id_type_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.type = 'test'

    res = sync_es._id_type_dict(obj)

    assert res == {
        'id': str(obj.id),
        'type': obj.type,
    }


def test_contact_dict():
    """Tests contact_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'

    res = sync_es._contact_dict(obj)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
    }


def test_company_dict():
    """Tests company_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.company_number = '01234567'

    res = sync_es._company_dict(obj)

    assert res == {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


def test_model_to_dict():
    """Tests _model_to_dict."""
    obj = mock.Mock()
    obj.a = 123
    obj.b = 456
    obj.c = 'what?'
    obj._meta = type('_Meta', (object,), {})()
    obj._meta.get_fields = lambda: []

    fields_column_fn = sync_es.FieldsColumnFn(fields=('a', 'b'),
                                              fn=lambda col: str(col)),

    res = sync_es._model_to_dict(obj, fields_column_fn=fields_column_fn)

    assert res['a'] == str(obj.a)
    assert res['b'] == str(obj.b)
    assert 'c' not in res


def test_es_document():
    """Tests _es_document."""
    doc_type = 'company'
    source = {
        'id': '123',
        'cat': 'meow',
    }
    res = sync_es._es_document(doc_type, source)

    assert res == {
        '_index': settings.ES_INDEX,
        '_type': doc_type,
        '_id': source.get('id'),
        '_source': source
    }


@mock.patch('datahub.search.management.commands.sync_es._model_to_dict')
def test_models_to_dict(model_to_dict):
    """Tests _models_to_dict."""
    model_to_dict.return_value = {
        'cat': 'meow'
    }

    data = (
        {}, {}
    )

    res = list(sync_es._models_to_dict(data))

    assert len(res) == 2


@mock.patch('datahub.search.management.commands.sync_es._es_document')
def test_dict_to_es(es_document):
    """Tests _dict_to_es."""
    es_document.return_value = {}
    doc_type = 'company'
    data = ({}, {})
    res = list(sync_es._dict_to_es(doc_type, data))

    assert len(res) == 2


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
        sync_es.DataSet((CompanyFactory(), CompanyFactory(),), sync_es.ESCompany),
        sync_es.DataSet((ContactFactory(),), sync_es.ESContact),
    )

    management.call_command(sync_es.Command(), batch_size=1)

    assert bulk.call_count == 3
