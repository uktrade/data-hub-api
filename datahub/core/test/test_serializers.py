from datetime import date
from unittest.mock import call, MagicMock, Mock
from uuid import uuid4

import pytest
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import IntegerField

from datahub.core.serializers import NestedRelatedField, RelaxedDateField, RelaxedURLField


class TestNestedRelatedField:
    """Tests related to NestedRelatedField."""

    def test_to_internal_dict(self):
        """Tests that model instances are returned for a dict with an 'id' key."""
        model = MagicMock()
        field = NestedRelatedField(model)
        uuid_ = uuid4()
        assert field.to_internal_value({'id': str(uuid_)})
        assert model.objects.all().get.call_args_list == [call(pk=uuid_)]

    def test_to_internal_str(self):
        """Tests that model instances are returned for a dict with an 'id' key."""
        model = MagicMock()
        field = NestedRelatedField(model)
        uuid_ = uuid4()
        assert field.to_internal_value(str(uuid_))
        assert model.objects.all().get.call_args_list == [call(pk=uuid_)]

    def test_to_internal_invalid_id(self):
        """Tests that a dict with an invalid UUID raises an exception."""
        model = MagicMock()
        field = NestedRelatedField(model)
        with pytest.raises(ValidationError):
            field.to_internal_value({'id': 'xxx'})

    def test_to_internal_no_id(self):
        """Tests that a dict without an id raises an exception."""
        model = MagicMock()
        field = NestedRelatedField(model)
        with pytest.raises(ValidationError):
            field.to_internal_value({})

    def test_to_internal_wrong_type(self):
        """Tests that a non-dict value raises an exception."""
        model = MagicMock()
        field = NestedRelatedField(model)
        with pytest.raises(ValidationError):
            field.to_internal_value([])

    def test_to_internal_non_existent_id(self):
        """Tests an id of a non-existent object raises an exception."""
        model = MagicMock()
        model.objects().all.get.return_value = ObjectDoesNotExist
        field = NestedRelatedField(model)
        with pytest.raises(ValidationError):
            field.to_internal_value({})

    def test_to_representation(self):
        """Tests that a model instance is converted to a dict."""
        model = Mock()
        uuid_ = uuid4()
        instance = Mock(id=uuid_, pk=uuid_)
        instance.name = 'instance name'
        field = NestedRelatedField(model)
        assert field.to_representation(instance) == {
            'id': str(instance.id),
            'name': instance.name,
        }

    def test_to_representation_extra_fields(self):
        """Tests that a model instance is converted to a dict with extra fields."""
        model = Mock()
        uuid_ = uuid4()
        uuid2_ = uuid4()
        instance = Mock(id=uuid_, pk=uuid_, test_field='12as', test2=uuid2_, test3='10')
        field = NestedRelatedField(
            model,
            extra_fields=(
                'test_field',
                'test2',
                ('test3', IntegerField()),
            ),
        )
        assert field.to_representation(instance) == {
            'id': str(instance.id),
            'test_field': instance.test_field,
            'test2': uuid2_,
            'test3': 10,
        }

    def test_to_representation_extra_fields_with_nested_related(self):
        """
        Tests that if the field has a nested related field,
        `to_representation` returns '<nested-field>': {...} using the nested mapping.
        """
        nested_pk = uuid4()
        nested_instance = Mock(id=nested_pk, pk=nested_pk, field1='field1_value')
        nested_field = NestedRelatedField(
            Mock(),
            extra_fields=(
                'field1',
            ),
        )

        instance_pk = uuid4()
        instance = Mock(id=instance_pk, pk=instance_pk, nested_instance=nested_instance)
        field = NestedRelatedField(
            Mock(),
            extra_fields=(
                ('nested_instance', nested_field),
            ),
        )
        assert field.to_representation(instance) == {
            'id': str(instance.id),
            'nested_instance': {
                'id': str(nested_pk),
                'field1': 'field1_value',
            },
        }

    def test_to_representation_extra_fields_with_nested_related_none(self):
        """
        Tests that if the field has a nested related field and its value is
        None, `to_representation` returns '<nested-field>': None.
        """
        nested_field = NestedRelatedField(
            Mock(),
            extra_fields=(
                'field1',
            ),
        )

        instance_pk = uuid4()
        instance = Mock(id=instance_pk, pk=instance_pk, nested_instance=None)
        field = NestedRelatedField(
            Mock(),
            extra_fields=(
                ('nested_instance', nested_field),
            ),
        )
        assert field.to_representation(instance) == {
            'id': str(instance.id),
            'nested_instance': None,
        }

    def test_to_choices(self):
        """Tests that model choices are returned."""
        model = Mock()
        uuid_ = uuid4()
        instance = Mock(id=uuid_, pk=uuid_)
        instance.name = 'instance name'
        model.objects.all.return_value = [instance] * 2
        field = NestedRelatedField(model)
        assert (list(field.get_choices().items()) == [(str(instance.id), str(instance))] * 2)

    def test_to_choices_limit(self):
        """Tests that model choices are limited and returned."""
        model = Mock()
        uuid_ = uuid4()
        instance = Mock(id=uuid_, pk=uuid_)
        instance.name = 'instance name'
        model.objects.all.return_value = [instance] * 2
        field = NestedRelatedField(model)
        assert list(field.get_choices(1).items()) == [(
            str(instance.id),
            str(instance),
        )]

        @pytest.mark.parametrize(
            'input_website,expected_website', (
                ('www.google.com', 'http://www.google.com'),
                ('http://www.google.com', 'http://www.google.com'),
                ('https://www.google.com', 'https://www.google.com'),
                ('', ''),
            ),
        )
        def test_url_field_input(self, input_website, expected_website):
            """Tests that RelaxedURLField prepends http:// when one is not provided."""
            assert RelaxedURLField().run_validation(input_website) == expected_website

        @pytest.mark.parametrize(
            'input_website,expected_website', (
                ('www.google.com', 'http://www.google.com'),
                ('http://www.google.com', 'http://www.google.com'),
                ('https://www.google.com', 'https://www.google.com'),
                ('', ''),
            ),
        )
        def test_url_field_output(self, input_website, expected_website):
            """Tests that RelaxedURLField prepends http:// when one is not stored."""
            assert RelaxedURLField().to_representation(input_website) == expected_website


class TestRelaxedDateField:
    """Tests for RelaxedDateField."""

    @pytest.mark.parametrize(
        'input_value,expected_date',
        (
            ('2018-01-10', date(2018, 1, 10)),
            ('2018-1-10', date(2018, 1, 10)),
            ('2018-10-1', date(2018, 10, 1)),
            ('2018/01/10', date(2018, 1, 10)),
            ('2018/1/10', date(2018, 1, 10)),
            ('2018/10/1', date(2018, 10, 1)),
        ),
    )
    def test_parses_dates(self, input_value, expected_date):
        """Test that various input values are parsed and interpreted as the correct date."""
        field = RelaxedDateField()
        assert field.to_internal_value(input_value) == expected_date
