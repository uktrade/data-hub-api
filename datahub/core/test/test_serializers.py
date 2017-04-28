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
    instance = Mock(id=uuid_, pk=uuid_, test_field='12as')
    field = NestedRelatedField(model, extra_fields=('test_field',))
    assert field.to_representation(instance) == {
        'id': str(instance.id),
        'test_field': instance.test_field
    }
