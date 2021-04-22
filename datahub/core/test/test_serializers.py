from datetime import date
from unittest.mock import call, MagicMock, Mock
from uuid import uuid4

import pytest
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from rest_framework.serializers import IntegerField

from datahub.core.constants import Country
from datahub.core.serializers import NestedRelatedField, RelaxedDateField, RelaxedURLField
from datahub.core.test.support.factories import MultiAddressModelFactory
from datahub.core.test_utils import APITestMixin


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
        """Tests that model instances are returned for a string."""
        model = MagicMock()
        field = NestedRelatedField(model)
        uuid_ = uuid4()
        assert field.to_internal_value(str(uuid_))
        assert model.objects.all().get.call_args_list == [call(pk=uuid_)]

    def test_to_internal_uuid(self):
        """Tests that model instances are returned for a UUID."""
        model = Mock()
        field = NestedRelatedField(model)
        uuid_ = uuid4()
        assert field.to_internal_value(uuid_)
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


@pytest.mark.urls('datahub.core.test.support.urls')
class TestAddressSerializer(APITestMixin):
    """Tests for the AddressSerializer."""

    @pytest.mark.parametrize(
        'post_data,expected_response',
        (
            # only primary address
            (
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                },
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # minimal primary address
            (
                {
                    'primary_address': {
                        'line_1': '2',
                        'town': 'London',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                },
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': '',
                        'town': 'London',
                        'postcode': '',
                        'county': '',
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # primary and secondary address
            (
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                    'secondary_address': {
                        'line_1': '1',
                        'line_2': 'Hello st.',
                        'town': 'Muckamore',
                        'county': 'Antrim',
                        'postcode': 'BT41 4QE',
                        'country': {'id': Country.ireland.value.id},
                    },
                },
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': {
                        'area': None,
                        'line_1': '1',
                        'line_2': 'Hello st.',
                        'town': 'Muckamore',
                        'county': 'Antrim',
                        'postcode': 'BT41 4QE',
                        'country': {
                            'id': '736a9ab2-5d95-e211-a939-e4115bead28a',
                            'name': 'Ireland',
                        },
                    },
                },
            ),

            # secondary address = None
            (
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                    'secondary_address': None,
                },
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # secondary address: all fields reset
            (
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                    'secondary_address': {
                        'line_1': '',
                        'line_2': '',
                        'town': '',
                        'county': '',
                        'postcode': '',
                        'country': None,
                    },
                },
                {
                    'primary_address': {
                        'area': None,
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),
        ),
    )
    def test_create(self, post_data, expected_response):
        """Tests for creating a model using the address serializer."""
        url = reverse('test-addresses-collection')
        response = self.api_client.post(url, data=post_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        'post_data,expected_errors',
        (
            # primary address: required
            (
                {},
                {
                    'primary_address': ['This field is required.'],
                },
            ),

            # primary address: can't be None
            (
                {
                    'primary_address': None,
                },
                {
                    'primary_address': ['This field may not be null.'],
                },
            ),

            # primary address: can't be {}
            (
                {
                    'primary_address': {},
                },
                {
                    'primary_address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),

            # primary address: line_1, town and country required when only one passed in
            (
                {
                    'primary_address': {
                        'line_1': '1',
                    },
                },
                {
                    'primary_address': {
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),

            # primary address: line_1, town and country required when optional field passed in
            (
                {
                    'primary_address': {
                        'county': 'London',
                    },
                },
                {
                    'primary_address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),

            # county can't be None
            (
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': '',
                        'town': 'London',
                        'county': None,
                        'postcode': 'SE10 9NN',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                },
                {
                    'primary_address': {
                        'county': ['This field may not be null.'],
                    },
                },
            ),

            # line_1 too long
            (
                {
                    'primary_address': {
                        'line_1': '2' * 256,
                        'town': 'London',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                },
                {
                    'primary_address': {
                        'line_1': ['Ensure this field has no more than 255 characters.'],
                    },
                },
            ),

            # secondary address: line_1, town and country required when only one passed in
            (
                {
                    'primary_address': {
                        'line_1': '2',
                        'town': 'London',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                    'secondary_address': {
                        'line_1': '1',
                    },
                },
                {
                    'secondary_address': {
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),

            # secondary address: line_1, town and country required when optional one passed in
            (
                {
                    'primary_address': {
                        'line_1': '2',
                        'town': 'London',
                        'country': {'id': Country.united_kingdom.value.id},
                    },
                    'secondary_address': {
                        'county': 'London',
                    },
                },
                {
                    'secondary_address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),
        ),
    )
    def test_create_validation(self, post_data, expected_errors):
        """Tests for validation errors when creating a model using an address serializer."""
        url = reverse('test-addresses-collection')
        response = self.api_client.post(url, data=post_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors

    @pytest.mark.parametrize(
        'initial_model_values,patch_data,expected_response',
        (
            # primary address: update line_1
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area': None,
                    'primary_address_area_id': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_area': None,
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': {
                        'line_1': '3',
                    },
                },
                {
                    'primary_address': {
                        'line_1': '3',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # primary address: reset non-required fields
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area_id': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_area_id': None,
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': {
                        'line_2': '',
                        'county': '',
                        'postcode': '',
                    },
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': '',
                        'town': 'London',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # secondary address: update line_1
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area_id': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '1',
                    'secondary_address_2': 'Hello st.',
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': 'Antrim',
                    'secondary_address_postcode': 'BT41 4QE',
                    'secondary_address_area_id': None,
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'secondary_address': {
                        'line_1': '4',
                    },
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': {
                        'line_1': '4',
                        'line_2': 'Hello st.',
                        'town': 'Muckamore',
                        'county': 'Antrim',
                        'postcode': 'BT41 4QE',
                        'area': None,
                        'country': {
                            'id': '736a9ab2-5d95-e211-a939-e4115bead28a',
                            'name': 'Ireland',
                        },
                    },
                },
            ),

            # secondary address: set to None
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,
                    'primary_address_area_id': None,

                    'secondary_address_1': '1',
                    'secondary_address_2': 'Hello st.',
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': 'Antrim',
                    'secondary_address_postcode': 'BT41 4QE',
                    'secondary_address_area_id': None,
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'secondary_address': None,
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # secondary address: reset non-required fields
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area_id': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '1',
                    'secondary_address_2': 'Hello st.',
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': 'Antrim',
                    'secondary_address_postcode': 'BT41 4QE',
                    'secondary_address_area_id': None,
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'secondary_address': {
                        'line_2': '',
                        'county': '',
                        'postcode': '',
                    },
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': {
                        'line_1': '1',
                        'line_2': '',
                        'town': 'Muckamore',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': '736a9ab2-5d95-e211-a939-e4115bead28a',
                            'name': 'Ireland',
                        },
                    },
                },
            ),

            # secondary address: reset all fields
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area_id': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '1',
                    'secondary_address_2': 'Hello st.',
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': 'Antrim',
                    'secondary_address_postcode': 'BT41 4QE',
                    'secondary_address_area_id': None,
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'secondary_address': {
                        'line_1': '',
                        'line_2': '',
                        'town': '',
                        'county': '',
                        'postcode': '',
                        'country': None,
                    },
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),
        ),
    )
    def test_update(self, initial_model_values, patch_data, expected_response):
        """Tests updating a model using an address serializer."""
        instance = MultiAddressModelFactory(**initial_model_values)
        url = reverse('test-addresses-item', kwargs={'pk': instance.pk})
        response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        'initial_model_values,patch_data,expected_errors',
        (
            # primary address: can't be None
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': None,
                },
                {
                    'primary_address': ['This field may not be null.'],
                },
            ),

            # primary address: line_1 required
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': {
                        'line_1': '',
                        'line_2': '',
                        'line_county': '',
                        'line_postcode': '',
                    },
                },
                {
                    'primary_address': {
                        'line_1': ['This field is required.'],
                    },
                },
            ),

            # county can't be None
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': {
                        'county': None,
                    },
                },
                {
                    'primary_address': {
                        'county': ['This field may not be null.'],
                    },
                },
            ),

            # line_1 too long
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': {
                        'line_1': 'a' * 256,
                    },
                },
                {
                    'primary_address': {
                        'line_1': ['Ensure this field has no more than 255 characters.'],
                    },
                },
            ),

            # secondary address: line_1, town and country required when only one passed in
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_country_id': None,
                },
                {
                    'secondary_address': {
                        'line_1': '1',
                    },
                },
                {
                    'secondary_address': {
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),

            # secondary address: line_1, town and country required when optional one passed in
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_country_id': None,
                },
                {
                    'secondary_address': {
                        'county': 'Wimbledon',
                    },
                },
                {
                    'secondary_address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),

            # secondary address: line_1, town and country required when blank values passed in
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '1',
                    'secondary_address_2': 'Hello st.',
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': 'Antrim',
                    'secondary_address_postcode': 'BT41 4QE',
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'secondary_address': {
                        'line_1': '',
                        'town': '',
                    },
                },
                {
                    'secondary_address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                    },
                },
            ),
        ),
    )
    def test_update_validation(self, initial_model_values, patch_data, expected_errors):
        """Tests for validation errors when updating a model using an address serializer."""
        instance = MultiAddressModelFactory(**initial_model_values)
        url = reverse('test-addresses-item', kwargs={'pk': instance.pk})
        response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors

    @pytest.mark.parametrize(
        'initial_model_values,expected_response',
        (
            # primary address only
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '',
                    'secondary_address_2': '',
                    'secondary_address_town': '',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_area': None,
                    'secondary_address_country_id': None,
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': None,
                },
            ),

            # primary and secondary address
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': 'Main Road',
                    'primary_address_town': 'London',
                    'primary_address_county': 'Greenwich',
                    'primary_address_postcode': 'SE10 9NN',
                    'primary_address_area': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '1',
                    'secondary_address_2': 'Hello st.',
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': 'Antrim',
                    'secondary_address_postcode': 'BT41 4QE',
                    'secondary_address_area': None,
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': {
                        'line_1': '1',
                        'line_2': 'Hello st.',
                        'town': 'Muckamore',
                        'county': 'Antrim',
                        'postcode': 'BT41 4QE',
                        'area': None,
                        'country': {
                            'id': '736a9ab2-5d95-e211-a939-e4115bead28a',
                            'name': 'Ireland',
                        },
                    },
                },
            ),

            # some fields as None instead of ''
            (
                {
                    'primary_address_1': '2',
                    'primary_address_2': '',
                    'primary_address_town': 'London',
                    'primary_address_county': None,
                    'primary_address_postcode': '',
                    'primary_address_area': None,
                    'primary_address_country_id': Country.united_kingdom.value.id,

                    'secondary_address_1': '1',
                    'secondary_address_2': None,
                    'secondary_address_town': 'Muckamore',
                    'secondary_address_county': '',
                    'secondary_address_postcode': '',
                    'secondary_address_area': None,
                    'secondary_address_country_id': Country.ireland.value.id,
                },
                {
                    'primary_address': {
                        'line_1': '2',
                        'line_2': '',
                        'town': 'London',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                            'name': 'United Kingdom',
                        },
                    },
                    'secondary_address': {
                        'line_1': '1',
                        'line_2': '',
                        'town': 'Muckamore',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': '736a9ab2-5d95-e211-a939-e4115bead28a',
                            'name': 'Ireland',
                        },
                    },
                },
            ),
        ),
    )
    def test_get(self, initial_model_values, expected_response):
        """Tests for getting a model using an address serializer."""
        instance = MultiAddressModelFactory(**initial_model_values)
        url = reverse('test-addresses-item', kwargs={'pk': instance.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response
