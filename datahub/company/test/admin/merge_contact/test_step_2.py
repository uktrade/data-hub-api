from unittest.mock import patch

import pytest

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import NON_FIELD_ERRORS
from django.test.html import parse_html
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Contact
from datahub.company.test.factories import ArchivedContactFactory, ContactFactory
from datahub.core.test_utils import AdminTestMixin
from datahub.core.utils import reverse_with_query_string


class TestSelectPrimaryContactViewGet(AdminTestMixin):
    """Tests form rendering in the 'Select primary contact' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'contact_1': '12345',
                'contact_2': '64567',
            },
            {
                'contact_1': '',
                'contact_2': '',
            },
            {
                'contact_1': '12345',
            },
            {
                'contact_1': lambda: str(ContactFactory().pk),
                'contact_2': '64567',
            },
            {
                'contact_1': '13495',
                'contact_2': lambda: str(ContactFactory().pk),
            },
        ),
    )
    def test_returns_400_if_invalid_contacts_passed(self, data):
        """
        Test that a 400 is returned when invalid values are passed for contact_1 or contact_2.

        This could only happen if the query string was manipulated, or one of the referenced
        contacts was deleted.
        """
        for key, value in data.items():
            if callable(value):
                data[key] = value()

        select_primary_route_name = admin_urlname(Contact._meta, 'merge-select-primary-contact')
        select_primary_url = reverse(select_primary_route_name)

        response = self.client.get(select_primary_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'swap', (True, False),
    )
    @pytest.mark.parametrize(
        'contact_1_factory,contact_2_factory',
        (
            (
                ArchivedContactFactory,
                ContactFactory,
            ),
        ),
        ids=[
            'archived-contact',
        ],
    )
    def test_radio_button_correctly_enabled_or_disabled(
        self,
        contact_1_factory,
        contact_2_factory,
        swap,
    ):
        """
        Tests that the radio button to select a contact is disabled if it is archived
        """
        contact_1 = (contact_2_factory if swap else contact_1_factory)()
        contact_2 = (contact_1_factory if swap else contact_2_factory)()
        contact_1_disabled = not swap
        contact_2_disabled = swap

        select_primary_route_name = admin_urlname(Contact._meta, 'merge-select-primary-contact')
        select_primary_url = reverse(select_primary_route_name)

        response = self.client.get(
            select_primary_url,
            data={
                'id_1': str(contact_1.pk),
                'id_2': str(contact_2.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK

        expected_radio_1_html = _get_radio_html(1, contact_1_disabled)
        assert _html_count_occurrences(expected_radio_1_html, response.rendered_content) == 1

        expected_radio_2_html = _get_radio_html(2, contact_2_disabled)
        assert _html_count_occurrences(expected_radio_2_html, response.rendered_content) == 1


class TestSelectPrimaryContactViewPost(AdminTestMixin):
    """Tests form submission in the 'Select primary contact' view."""

    @pytest.mark.parametrize('selected_contact', ('1', '2'))
    def test_proceeds_if_contact_chosen(self, selected_contact):
        """Test that if a valid selection is made, the user is redirected to the change list."""
        contact_1 = ContactFactory()
        contact_2 = ContactFactory()

        select_primary_route_name = admin_urlname(Contact._meta, 'merge-select-primary-contact')
        select_primary_query_args = {
            'id_1': str(contact_1.pk),
            'id_2': str(contact_2.pk),
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        response = self.client.post(
            select_primary_url,
            follow=True,
            data={
                'selected_model': selected_contact,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        confirm_merge_route_name = admin_urlname(Contact._meta, 'merge-confirm')
        confirm_merge_query_args = {
            'source': (contact_1 if selected_contact != '1' else contact_2).pk,
            'target': (contact_1 if selected_contact == '1' else contact_2).pk,
        }
        confirm_merge_url = reverse_with_query_string(
            confirm_merge_route_name,
            confirm_merge_query_args,
        )

        assert response.redirect_chain[0][0] == confirm_merge_url

    @pytest.mark.parametrize('swap', (False, True))
    @pytest.mark.parametrize(
        'contact_1_factory, contact_2_factory, expected_error, disallowed_fields',
        (
            (
                ArchivedContactFactory,
                ContactFactory,
                'The contact selected is archived.',
                [],
            ),
        ),
    )
    @patch('datahub.company.merge_contact.is_model_a_valid_merge_source')
    def test_error_displayed_if_invalid_selection_made(
        self,
        is_model_a_valid_merge_source_mock,
        swap,
        contact_1_factory,
        contact_2_factory,
        expected_error,
        disallowed_fields,
    ):
        expected_error_message = expected_error
        if disallowed_fields:
            expected_error_message += f': Invalid object: {disallowed_fields}'

        """Tests that if an invalid selection is submitted, an error is returned."""
        contact_1 = (contact_2_factory if swap else contact_1_factory)()
        contact_2 = (contact_1_factory if swap else contact_2_factory)()
        selected_contact = 2 if swap else 1

        select_primary_route_name = admin_urlname(Contact._meta, 'merge-select-primary-contact')
        select_primary_query_args = {
            'id_1': str(contact_1.pk),
            'id_2': str(contact_2.pk),
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        response = self.client.post(
            select_primary_url,
            data={
                'model_1': str(contact_1.pk),
                'model_2': str(contact_2.pk),
                'selected_model': selected_contact,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        form = response.context['form']
        assert form.errors == {
            NON_FIELD_ERRORS: [expected_error_message],
        }


def _get_radio_html(index, disabled):
    extra_attrs = ' disabled' if disabled else ''
    return f"""<input name="selected_model" value="{index}" required="" \
id="id_selected_model_radio_{index}" type="radio" {extra_attrs}>"""


def _html_count_occurrences(needle, haystack):
    parsed_haystack = parse_html(haystack)
    parsed_needle = parse_html(needle)
    return parsed_haystack.count(parsed_needle)
