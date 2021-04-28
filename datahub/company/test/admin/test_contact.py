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
            # Dialling code should be entered separately
            '+44 116289',
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
            'telephone_countrycode': contact.telephone_countrycode,
            'email': contact.email,
            'telephone_number': telephone_number,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.OK
        form_errors = response.context_data['adminform'].errors
        assert 'telephone_number' in form_errors
        assert form_errors['telephone_number'] == [
            'Phone number must be composed of numeric characters. Country code should be entered '
            'separately.',
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
            'telephone_countrycode': contact.telephone_countrycode,
            'email': contact.email,
            'telephone_number': telephone_number,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.FOUND

    @pytest.mark.parametrize(
        'telephone_alternative',
        (
            '$12 Number',
            '01234 ($)',
        ),
    )
    def test_invalid_alternative_phone_numbers(self, telephone_alternative):
        """Invalid alt phone numbers should raise a validation error."""
        contact = ContactFactory()
        url = reverse('admin:company_contact_change', args=(contact.id,))
        data = {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'telephone_countrycode': contact.telephone_countrycode,
            'email': contact.email,
            'telephone_number': contact.telephone_number,
            'telephone_alternative': telephone_alternative,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.OK
        form_errors = response.context_data['adminform'].errors
        assert 'telephone_alternative' in form_errors
        assert form_errors['telephone_alternative'] == [
            'Phone number must be composed of numeric characters.',
        ]

    @pytest.mark.parametrize(
        'telephone_alternative',
        (
            '1112223',
            '123 456',
            '(0) 123 456',
            # Dialling code is allowed because there is no separate field for it
            '+44 116289',
        ),
    )
    def test_valid_alternative_phone_numbers(self, telephone_alternative):
        """Valid alt phone numbers should be redirected."""
        contact = ContactFactory()
        url = reverse('admin:company_contact_change', args=(contact.id,))
        data = {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'telephone_countrycode': contact.telephone_countrycode,
            'email': contact.email,
            'telephone_number': contact.telephone_number,
            'telephone_alternative': telephone_alternative,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.FOUND

    @pytest.mark.parametrize(
        'country_code',
        (
            # Too long
            '12345',
            '+12345',
            # A string
            '+UK',
        ),
    )
    def test_invalid_telephone_country_code(self, country_code):
        """Invalid country codes should raise a validation error."""
        contact = ContactFactory()
        url = reverse('admin:company_contact_change', args=(contact.id,))
        data = {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'telephone_countrycode': country_code,
            'email': contact.email,
            'telephone_number': contact.telephone_number,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.OK
        form_errors = response.context_data['adminform'].errors
        assert 'telephone_countrycode' in form_errors
        assert form_errors['telephone_countrycode'] == [
            'Country code should consist of one to four numbers',
        ]

    @pytest.mark.parametrize(
        'country_code',
        (
            '44',
            '+44',
            '1',
            '+1',
            '+998',
            '+1242',
            '1567',
        ),
    )
    def test_valid_telephone_country_code(self, country_code):
        """Valid country codes should be redirected."""
        contact = ContactFactory()
        url = reverse('admin:company_contact_change', args=(contact.id,))
        data = {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'telephone_countrycode': contact.telephone_countrycode,
            'email': contact.email,
            'telephone_number': contact.telephone_number,
        }

        response = self.client.post(url, data)
        assert response.status_code == HTTPStatus.FOUND
