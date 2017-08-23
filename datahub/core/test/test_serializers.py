from unittest.mock import call, MagicMock, Mock
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from reversion.models import Version

from datahub.core.serializers import AuditSerializer, NestedRelatedField


def test_audit_log_diff_algo():
    """Test simple diff algorithm."""
    given = {
        'old': {
            'field1': 'val1',
            'field2': 'val2',
        },
        'new': {
            'field1': 'val1',
            'field2': 'new-val',
            'field3': 'added',
        },
    }

    expected = {
        'field2': ['val2', 'new-val'],
        'field3': [None, 'added'],
    }

    assert AuditSerializer._diff_versions(given['old'], given['new']) == expected


@pytest.mark.parametrize('num_versions,offset,limit,exp_results,exp_next,exp_previous', (
    (26, '', '', range(0, 25), None, None),
    (26, '10', '10', range(10, 20), 'http://test/audit?offset=20&limit=10',
     'http://test/audit?limit=10'),
    (26, '20', '10', range(20, 25), None, 'http://test/audit?offset=10&limit=10'),
))
def test_audit_log_pagination(num_versions, offset, limit, exp_results, exp_next, exp_previous,
                              monkeypatch):
    """Test the audit log pagination."""
    monkeypatch.setattr(
        Version.objects, 'get_for_object', _create_get_for_object_stub(num_versions)
    )
    instance = Mock()
    request = Mock(
        build_absolute_uri=lambda: 'http://test/audit',
        query_params={
            'offset': offset,
            'limit': limit
        })
    context = {
        'request': request
    }
    serializer = AuditSerializer(context=context)
    response_data = serializer.to_representation(instance)
    results = response_data['results']

    assert response_data['count'] == max(num_versions - 1, 0)
    assert _create_canonical_url_object(response_data['next']) == _create_canonical_url_object(
        exp_next)
    assert _create_canonical_url_object(response_data['previous']) == _create_canonical_url_object(
        exp_previous)
    assert [result['id'] for result in results] == list(exp_results)


class _VersionQuerySetStub:
    """VersionQuerySet stub."""

    def __init__(self, count):
        """Initialises the instance, creating some stub version instances to return as results."""
        self.items = [MagicMock(id=n) for n in range(count)]

    def __getitem__(self, item):
        """Returns items from the fake data generated."""
        return self.items[item]

    def __len__(self):
        """Returns the number of items generated."""
        return len(self.items)

    def count(self):
        """Returns the number of items generated."""
        return len(self.items)


def _create_get_for_object_stub(num_versions):
    """Creates a stub replacement for Version.objects.get_for_object."""
    def mock_versions(obj, model_db=None):
        return _VersionQuerySetStub(num_versions)

    return mock_versions


def _create_canonical_url_object(url):
    """Turns a URL into an object in a canonical form that can be used for comparisons."""
    if url is None:
        return None
    parse_results = urlparse(url)
    parsed_dict = parse_results._asdict()
    parsed_dict['query'] = parse_qs(parse_results.query)
    return parsed_dict


def test_nested_rel_field_to_internal_dict():
    """Tests that model instances are returned for a dict with an 'id' key."""
    model = MagicMock()
    field = NestedRelatedField(model)
    uuid_ = uuid4()
    assert field.to_internal_value({'id': str(uuid_)})
    assert model.objects.all().get.call_args_list == [call(pk=uuid_)]


def test_nested_rel_field_to_internal_str():
    """Tests that model instances are returned for a dict with an 'id' key."""
    model = MagicMock()
    field = NestedRelatedField(model)
    uuid_ = uuid4()
    assert field.to_internal_value(str(uuid_))
    assert model.objects.all().get.call_args_list == [call(pk=uuid_)]


def test_nested_rel_field_to_internal_invalid_id():
    """Tests that a dict with an invalid UUID raises an exception."""
    model = MagicMock()
    field = NestedRelatedField(model)
    with pytest.raises(ValidationError):
        field.to_internal_value({'id': 'xxx'})


def test_nested_rel_field_to_internal_no_id():
    """Tests that a dict without an id raises an exception."""
    model = MagicMock()
    field = NestedRelatedField(model)
    with pytest.raises(ValidationError):
        field.to_internal_value({})


def test_nested_rel_field_to_internal_wrong_type():
    """Tests that a non-dict value raises an exception."""
    model = MagicMock()
    field = NestedRelatedField(model)
    with pytest.raises(ValidationError):
        field.to_internal_value([])


def test_nested_rel_field_to_internal_non_existent_id():
    """Tests an id of a non-existent object raises an exception."""
    model = MagicMock()
    model.objects().all.get.return_value = ObjectDoesNotExist
    field = NestedRelatedField(model)
    with pytest.raises(ValidationError):
        field.to_internal_value({})


def test_nested_rel_field_to_repr():
    """Tests that a model instance is converted to a dict."""
    model = Mock()
    uuid_ = uuid4()
    instance = Mock(id=uuid_, pk=uuid_)
    instance.name = 'instance name'
    field = NestedRelatedField(model)
    assert field.to_representation(instance) == {
        'id': str(instance.id),
        'name': instance.name
    }


def test_nested_rel_field_to_repr_extra_fields():
    """Tests that a model instance is converted to a dict with extra fields."""
    model = Mock()
    uuid_ = uuid4()
    uuid2_ = uuid4()
    instance = Mock(id=uuid_, pk=uuid_, test_field='12as', test2=uuid2_)
    field = NestedRelatedField(model, extra_fields=('test_field', 'test2'))
    assert field.to_representation(instance) == {
        'id': str(instance.id),
        'test_field': instance.test_field,
        'test2': str(uuid2_)
    }


def test_nested_rel_field_to_choices():
    """Tests that model choices are returned."""
    model = Mock()
    uuid_ = uuid4()
    instance = Mock(id=uuid_, pk=uuid_)
    instance.name = 'instance name'
    model.objects.all.return_value = [instance] * 2
    field = NestedRelatedField(model)
    assert (list(field.get_choices().items()) == [(str(instance.id),
                                                   str(instance))] * 2)


def test_nested_rel_field_to_choices_limit():
    """Tests that model choices are limited and returned."""
    model = Mock()
    uuid_ = uuid4()
    instance = Mock(id=uuid_, pk=uuid_)
    instance.name = 'instance name'
    model.objects.all.return_value = [instance] * 2
    field = NestedRelatedField(model)
    assert (list(field.get_choices(1).items()) == [(str(instance.id),
                                                    str(instance))])
