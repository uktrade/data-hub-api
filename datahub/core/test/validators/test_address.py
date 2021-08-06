from unittest import mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core.validators import AddressValidator


class TestAddressValidator:
    """Tests for the AddressValidator."""

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('with_instance', (True, False))
    def test_fails_without_any_fields_if_not_lazy(self, values_as_data, with_instance):
        """
        Test that the validation fails if lazy == False and the required fields
        are not specified.

        Test all scenarios:
        - with non-set fields on the instance and empty data
        - with non-set fields in the data param
        - with instance == None and empty data
        - with instance == None and non-set fields in the data param
        """
        address_fields = {
            'address1': None,
            'address2': None,
            'town': None,
        }

        instance = mock.Mock(**address_fields) if with_instance else None
        data = address_fields if values_as_data else {}

        validator = AddressValidator(
            lazy=False,
            fields_mapping={
                'address1': {'required': True},
                'address2': {'required': False},
                'town': {'required': True},
            },
        )
        serializer = mock.Mock(instance=instance)

        with pytest.raises(ValidationError) as exc:
            validator(data, serializer)
        assert exc.value.detail == {
            'address1': ['This field is required.'],
            'town': ['This field is required.'],
        }

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('with_instance', (True, False))
    def test_passes_without_any_fields_set_if_lazy(self, values_as_data, with_instance):
        """
        Test that the validation passes if lazy == True and none of the fields
        are specified.

        Test all scenarios:
        - with non-set fields on the instance and empty data
        - with non-set fields in the data param
        - with instance == None and empty data
        - with instance == None and non-set fields in the data param
        """
        address_fields = {
            'address1': None,
            'address2': None,
            'town': None,
        }

        instance = mock.Mock(**address_fields) if with_instance else None
        data = address_fields if values_as_data else {}

        validator = AddressValidator(
            lazy=True,
            fields_mapping={
                'address1': {'required': True},
                'address2': {'required': False},
                'town': {'required': True},
            },
        )
        serializer = mock.Mock(instance=instance)

        try:
            validator(data, serializer)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('lazy', (True, False))
    def test_fails_without_all_required_fields_set(self, values_as_data, lazy):
        """
        Test that the validation fails if only some fields are set but not
        all the required ones are.

        Test all scenarios:
        - with lazy == True and empty data
        - with lazy == True and only some fields set in data
        - with lazy == False and empty data
        - with lazy == False and only some fields set in data
        """
        address_fields = {
            'address1': None,
            'address2': 'lorem ipsum',
            'town': None,
        }

        instance = mock.Mock(**address_fields)
        data = address_fields if values_as_data else {}

        validator = AddressValidator(
            lazy=lazy,
            fields_mapping={
                'address1': {'required': True},
                'address2': {'required': False},
                'town': {'required': True},
            },
        )
        serializer = mock.Mock(instance=instance)

        with pytest.raises(ValidationError) as exc:
            validator(data, serializer)
        assert exc.value.detail == {
            'address1': ['This field is required.'],
            'town': ['This field is required.'],
        }

    def test_defaults(self):
        """Test the defaults props."""
        validator = AddressValidator()
        assert not validator.lazy
        assert validator.fields_mapping == validator.DEFAULT_FIELDS_MAPPING
