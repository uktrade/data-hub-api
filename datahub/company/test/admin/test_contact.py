from http import HTTPStatus

import pytest
from django.urls import reverse

from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import AdminTestMixin


pytestmark = pytest.mark.django_db


class TestContacts(AdminTestMixin):
    """Test that Contacts are properly validated"""

    @pytest.mark.parametrize(
        'telephone_number',
        [
            'abc-def-ghij',  # contains letter
            '+1 (555) abc-4567',  # mixed letters and numbers
            '++1 555 123 4567',  # multiple plus signs
            '+',  # only plus sign
            '555-123-4567 extension 123',  # 'extension' is not matched
            '+1 @555 123 4567',  # invalid special character
            '+1 555 123 4567 ext',  # ext without number
            'ext 123',  # only extension
            '+1 (555) 123-4567 ext 12b',  # letter in extension
        ],
    )
    def test_invalid_phone_numbers(self, telephone_number):
        """Invalid phone numbers should raise a validation error."""
        contact = ContactFactory()
        url = reverse('admin:company_contact_change', args=(contact.id,))
        data = {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'full_telephone_number': telephone_number,
            'email': contact.email,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.OK
        form_errors = response.context_data['adminform'].errors
        assert 'full_telephone_number' in form_errors
        error_message = (
            'Phone number must be composed of valid characters. '
            'These include: 0-9, spaces, hyphens, full stops, or open/close brackets, '
            'optionally preceded with a plus sign. Extensions can be included using '
            "'ext' or 'x' followed by digits."
        )
        assert form_errors['full_telephone_number'] == [error_message]

    @pytest.mark.parametrize(
        'telephone_number',
        [
            '+1 (555) 123-4567',
            '+44 20 7123 4567',
            '(0) 123 456',
            '555.123.4567',
            '1-555-123-4567',
            '+44 20 7123 4567 ext 890',
            '+1 55 123 4567 x123',
            '+49.123.456.7890',
        ],
    )
    def test_valid_phone_numbers(self, telephone_number):
        """Valid phone numbers should be redirected."""
        contact = ContactFactory()
        url = reverse('admin:company_contact_change', args=(contact.id,))
        data = {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'full_telephone_number': telephone_number,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.FOUND
