from unittest import mock
import pytest

from rest_framework.exceptions import ValidationError

from ..validators import ContactWorksAtCompanyValidator, ReadonlyAfterCreationValidator


class TestContactWorksAtCompanyValidator:
    """Tests for ContactWorksAtCompanyValidator."""

    def test_contact_from_company(self):
        """
        Test that if the contact specified in data works
        at the company specified in data, the validation passes.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_contact = mock.Mock(company=company)

        validator = ContactWorksAtCompanyValidator()
        validator.set_context(serializer)

        try:
            validator({
                'contact': new_contact,
                'company': company
            })
        except Exception:
            pytest.fail('Should not raise a validator error')

    def test_contact_not_from_company(self):
        """
        Test that if the contact specified in data doesn't works
        at the company specified in data, the validation fails.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_contact = mock.Mock()  # doesn't work at `company`

        validator = ContactWorksAtCompanyValidator()
        validator.set_context(serializer)

        with pytest.raises(ValidationError):
            validator({
                'contact': new_contact,
                'company': company
            })

    def test_with_different_field_names(self):
        """
        Test that the validation passes when using different field names.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_main_contact = mock.Mock(company=company)

        validator = ContactWorksAtCompanyValidator(
            contact_field='main_contact',
            company_field='main_company'
        )
        validator.set_context(serializer)

        try:
            validator({
                'main_contact': new_main_contact,
                'main_company': company
            })
        except Exception:
            pytest.fail('Should not raise a validator error')


class TestReadonlyAfterCreationValidator:
    """Tests for ReadonlyAfterCreationValidator."""

    def test_can_change_when_creating(self):
        """Test that if we are creating the instance, the validation passes."""
        serializer = mock.Mock(instance=None)

        validator = ReadonlyAfterCreationValidator(
            fields=('field1', 'field2')
        )
        validator.set_context(serializer)

        try:
            validator({
                'field1': 'some value',
                'field2': 'some value',
            })
        except Exception:
            pytest.fail('Should not raise a validator error')

    def test_cannot_change_after_creation(self):
        """
        Test that if we are updating the instance and we try to update the fields,
        the validation fails.
        """
        serializer = mock.Mock()  # serializer.instance is != None

        validator = ReadonlyAfterCreationValidator(
            fields=('field1', 'field2')
        )
        validator.set_context(serializer)

        with pytest.raises(ValidationError):
            validator({
                'field1': 'some value',
                'field2': 'some value',
            })

    def test_ok_if_the_values_dont_change_after_creation(self):
        """
        Test that if we are updating the instance and we don't update the fields,
        the validation passes.
        """
        serializer = mock.Mock()
        instance = serializer.instance

        validator = ReadonlyAfterCreationValidator(
            fields=('field1', 'field2')
        )
        validator.set_context(serializer)

        try:
            validator({
                'field1': instance.field1,
                'field2': instance.field2,
            })
        except Exception:
            pytest.fail('Should not raise a validator error')
