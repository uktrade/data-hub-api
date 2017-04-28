from unittest.mock import call, MagicMock, Mock
from uuid import uuid4

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core.serializers import NestedRelatedField


def test_nested_rel_field_to_internal():
    """Tests that model instances are returned for a dict with an 'id' key."""
    model = MagicMock()
    field = NestedRelatedField(model)
    uuid_ = uuid4()
    assert field.to_internal_value({'id': uuid_})
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
    assert list(field.get_choices().items()) == [({
        'id': str(instance.id),
        'name': instance.name
    }, str(instance))] * 2
