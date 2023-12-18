import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Contact, ContactPermission
from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.core.utils import reverse_with_query_string


class TestMergeWithAnotherContactLink(AdminTestMixin):
    """Tests the 'merge with another contact' link on the change form."""

    def test_link_exists(self):
        """Test that the link exists for a user with the change contact permission."""
        contact = ContactFactory()

        change_route_name = admin_urlname(Contact._meta, 'change')
        change_url = reverse(change_route_name, args=(contact.pk,))

        response = self.client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        select_other_route_name = admin_urlname(Contact._meta, 'merge-select-other-contact')
        select_other_query_args = {
            'id_1': contact.pk,
        }
        select_other_url = reverse_with_query_string(
            select_other_route_name,
            select_other_query_args,
        )

        assert select_other_url in response.rendered_content

    def test_link_does_not_exist_with_only_view_permission(self):
        """Test that the link does not exist for a user with only the view contact permission."""
        contact = ContactFactory()

        change_route_name = admin_urlname(Contact._meta, 'change')
        change_url = reverse(change_route_name, args=(contact.pk,))

        user = create_test_user(
            permission_codenames=(ContactPermission.view_contact,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        response = client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        select_other_route_name = admin_urlname(Contact._meta, 'merge-select-other-contact')
        select_other_url = reverse(select_other_route_name)

        assert select_other_url not in response.rendered_content


class TestMergeWithAnotherContactViewGet(AdminTestMixin):
    """Tests GET requests for the 'Merge with another contact' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'contact_1': '',
            },
            {
                'contact_1': '12345',
            },
        ),
    )
    def test_returns_400_if_invalid_contact_passed(self, data):
        """
        Test that a 400 is returned when an invalid value is passed in the query string.

        This could only happen if the query string was manipulated, or the referenced contact
        was deleted.
        """
        select_other_route_name = admin_urlname(Contact._meta, 'merge-select-other-contact')
        select_other_url = reverse(select_other_route_name)

        response = self.client.get(select_other_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_200_if_valid_contacts_passed(self):
        """Tests that a 200 is returned if a valid company is passed in the query string."""
        contact_1 = ContactFactory()

        select_other_route_name = admin_urlname(Contact._meta, 'merge-select-other-contact')
        select_other_url = reverse(select_other_route_name)

        response = self.client.get(
            select_other_url,
            data={
                'id_1': str(contact_1.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK


class TestMergeWithAnotherCompanyViewPost(AdminTestMixin):
    """Tests form submission for the 'Merge with another company' view."""

    SAME_CONTACT = object()

    def test_proceeds_if_valid_contact_provided(self):
        """Test the view redirects if a valid contact is provided."""
        main_contact = ContactFactory()
        other_contact = ContactFactory()

        select_other_route_name = admin_urlname(Contact._meta, 'merge-select-other-contact')
        select_other_query_args = {
            'id_1': main_contact.pk,
        }
        select_other_url = reverse_with_query_string(
            select_other_route_name,
            select_other_query_args,
        )

        response = self.client.post(
            select_other_url,
            follow=True,
            data={
                'id_2': str(other_contact.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        select_primary_route_name = admin_urlname(Contact._meta, 'merge-select-primary-contact')
        select_primary_query_args = {
            'id_1': main_contact.pk,
            'id_2': other_contact.pk,
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        assert response.redirect_chain[0][0] == select_primary_url

    @pytest.mark.parametrize(
        'contact_2,expected_error',
        (
            (
                SAME_CONTACT,
                'The two contacts to merge cannot be the same. Please select a different '
                'contact.',
            ),
            (
                '1234',
                '“1234” is not a valid UUID.',
            ),
            (
                '',
                'This field is required.',
            ),
        ),
    )
    def test_error_if_invalid_contact_selected(self, contact_2, expected_error):
        """Test that an error is displayed if the an invalid contact is selected."""
        contact = ContactFactory()

        select_other_route_name = admin_urlname(Contact._meta, 'merge-select-other-contact')
        select_other_query_args = {
            'id_1': contact.pk,
        }
        select_other_url = reverse_with_query_string(
            select_other_route_name,
            select_other_query_args,
        )

        value = str(contact.pk) if contact_2 is self.SAME_CONTACT else contact_2

        response = self.client.post(
            select_other_url,
            data={
                'id_2': value,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']

        assert 'id_2' in form.errors
        assert form.errors['id_2'] == [expected_error]
