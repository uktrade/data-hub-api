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
        (
            '$12 Number',
            '01234 ($)',
        ),
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
        assert form_errors['full_telephone_number'] == [
            'Phone number must be composed of numeric characters.',
        ]

    @pytest.mark.parametrize(
        'telephone_number',
        (
            '1112223',
            '123 456',
            '(0) 123 456',
        ),
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
