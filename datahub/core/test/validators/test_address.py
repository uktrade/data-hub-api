from unittest import mock
from unittest.mock import Mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core import constants
from datahub.core.validators import (
    AddressAreaValidator,
    AddressValidator,
)
from datahub.feature_flag.test.factories import FeatureFlagFactory

pytestmark = pytest.mark.django_db


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


class TestAddressAreaValidatorShould:
    """Tests for the AddressAreaValidator."""

    def test_by_default_no_error_is_raised(self):
        """Test empty object does not raise exception"""
        serializer = Mock(instance=Mock(address_country=None))
        validator = AddressAreaValidator()

        try:
            validator({}, serializer)
        except ValidationError:
            pytest.fail('Should not raise a validator error.')

    def test_by_default_with_feature_flag_no_error_is_raised(self):
        """Test empty object with feature flag set does not raise exception"""
        FeatureFlagFactory(code='address-area-contact-required-field')
        serializer = Mock(instance=Mock(address_country=None))
        validator = AddressAreaValidator()

        try:
            validator({}, serializer)
        except ValidationError:
            pytest.fail('Should not raise a validator error.')

    @pytest.mark.parametrize(
        'country_id, expected_response',
        (
            (
                constants.Country.united_states.value.id,
                {
                    'address_area': ['This field is required.'],
                },
            ),
            (
                constants.Country.canada.value.id,
                {
                    'address_area': ['This field is required.'],
                },
            ),
        ),
    )
    def test_area_required_validation_raised_for_ca_and_us(
        self,
        country_id,
        expected_response,
    ):
        """
        Ensure that area required validation is called for Canada and United States
        """
        FeatureFlagFactory(code='address-area-contact-required-field')
        data = {
            'address_country': {
                'id': country_id,
            },
        }
        serializer = Mock(instance=Mock(address_area=None))
        validator = AddressAreaValidator()

        with pytest.raises(ValidationError) as error:
            validator(data, serializer)

        assert error.value.args[1] == expected_response

    def test_other_countries_dont_raise_errors(self):
        """Test countries that are not united states or canada dont throw errors"""
        FeatureFlagFactory(code='address-area-contact-required-field')
        data = {
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
            },
        }
        serializer = Mock(instance=Mock(address_area=None))
        validator = AddressAreaValidator()

        try:
            validator(data, serializer)
        except ValidationError:
            pytest.fail('Should not raise a validator error for United Kingdom.')
