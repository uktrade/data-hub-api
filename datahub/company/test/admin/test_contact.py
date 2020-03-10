import io
from datetime import datetime

import factory
import pytest
from django.contrib import messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.test import Client
from django.urls import reverse
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from reversion.models import Version

from datahub.company.models import Contact, ContactPermission
from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user

pytestmark = pytest.mark.django_db


class TestContactAdminChangeList(AdminTestMixin):
    """Tests for the contact admin change list."""

    def test_load_opt_outs_link_exists(self):
        """
        Test that there is a link to load email marketing opt outs on the contact change list page.
        """
        change_list_url = reverse(admin_urlname(Contact._meta, 'changelist'))
        response = self.client.get(change_list_url)
        assert response.status_code == status.HTTP_200_OK

        load_opt_outs_url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )
        assert load_opt_outs_url in response.rendered_content

    def test_load_opt_outs_link_does_not_exist_if_only_has_view_permission(self):
        """
        Test that there is not a link to load email marketing opt outs if the user only has view
        (but not change) permission for contacts.
        """
        change_list_url = reverse(admin_urlname(Contact._meta, 'changelist'))
        user = create_test_user(
            permission_codenames=(ContactPermission.view_contact,),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(change_list_url)
        assert response.status_code == status.HTTP_200_OK

        load_opt_outs_url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )
        assert f'Select {Contact._meta.verbose_name} to view' in response.rendered_content
        assert load_opt_outs_url not in response.rendered_content


class TestContactAdminOptOutForm(AdminTestMixin):
    """Tests for the contact admin load email marketing opt outs form."""

    def test_redirects_to_login_page_if_not_logged_in(self):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )
        client = Client()
        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    def test_redirects_to_login_page_if_not_staff(self):
        """Test that the view redirects to the login page if the user isn't a member of staff."""
        url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )
        user = create_test_user(is_staff=False, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    def test_permission_denied_if_staff_and_without_change_permission(self):
        """
        Test that the view returns a 403 response if the staff user does not have the
        change contact permission.
        """
        url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )
        user = create_test_user(
            permission_codenames=(ContactPermission.view_contact,),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_does_not_allow_file_without_email_column(self):
        """Test that the form rejects a CSV file that doesn't contain an email column."""
        file = io.BytesIO(b'test\r\nrow')
        file.name = 'test.csv'

        url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )
        response = self.client.post(
            url,
            data={
                'csv_file': file,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']

        assert 'csv_file' in form.errors
        assert form.errors['csv_file'] == [
            'This file is missing the following required columns: email.',
        ]

    @pytest.mark.parametrize('encoding', ('utf-8', 'utf-8-sig'))
    def test_opts_out_contacts(self, encoding):
        """
        Test that accepts_dit_email_marketing is updated for the contacts specified in the CSV
        file.
        """
        filename = 'filea.csv'
        emails = [
            'test1@datahub',
            'test1@datahub',
            'test2@datahub',
            'test2@datahub',
            'test3@datahub',
            'test4@datahub',
        ]
        marketing_status = [True, True, True, False, True, True]
        creation_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            contacts = ContactFactory.create_batch(
                len(emails),
                email=factory.Iterator(emails),
                accepts_dit_email_marketing=factory.Iterator(marketing_status),
                modified_by=None,
            )

        file = io.BytesIO("""email\r
test1@datahub\r
TEST2@datahub\r
test6@datahub\r
""".encode(encoding=encoding))
        file.name = filename

        url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )

        post_time = datetime(2014, 5, 3, 19, 0, 16, tzinfo=utc)
        with freeze_time(post_time):
            response = self.client.post(
                url,
                follow=True,
                data={
                    'csv_file': file,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        change_list_url = reverse(admin_urlname(Contact._meta, 'changelist'))
        assert response.redirect_chain[0][0] == change_list_url

        for contact in contacts:
            contact.refresh_from_db()

        assert [contact.accepts_dit_email_marketing for contact in contacts] == [
            False, False, False, False, True, True,
        ]
        assert [contact.modified_on for contact in contacts] == [
            post_time, post_time, post_time, creation_time, creation_time, creation_time,
        ]
        assert [contact.modified_by for contact in contacts] == [
            self.user, self.user, self.user, None, None, None,
        ]

        messages = list(response.context['messages'])
        assert len(messages) == 2
        assert messages[0].level == django_messages.SUCCESS
        assert messages[0].message == (
            '3 contacts opted out of marketing emails and 1 contacts already opted out'
        )
        assert messages[1].level == django_messages.WARNING
        assert messages[1].message == '1 email addresses did not match a contact'

    def test_updates_audit_log(self):
        """Test that audit log entries are created for modified contacts."""
        creation_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            contact_with_change = ContactFactory(
                email='test1@datahub',
                accepts_dit_email_marketing=True,
            )
            contact_without_change = ContactFactory(
                email='test2@datahub',
                accepts_dit_email_marketing=True,
            )
            contact_already_opted_out = ContactFactory(
                email='test1@datahub',
                accepts_dit_email_marketing=False,
            )

        file = io.BytesIO("""email\r
test1@datahub\r
""".encode())
        file.name = 'test.csv'

        url = reverse(
            admin_urlname(Contact._meta, 'load-email-marketing-opt-outs'),
        )

        post_time = datetime(2014, 5, 3, 19, 0, 16, tzinfo=utc)
        with freeze_time(post_time):
            response = self.client.post(
                url,
                follow=True,
                data={
                    'csv_file': file,
                },
            )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        change_list_url = reverse(admin_urlname(Contact._meta, 'changelist'))
        assert response.redirect_chain[0][0] == change_list_url

        versions = Version.objects.get_for_object(contact_with_change)
        assert versions.count() == 1
        assert versions[0].revision.get_comment() == 'Loaded bulk email opt-out list.'

        versions = Version.objects.get_for_object(contact_without_change)
        assert versions.count() == 0

        versions = Version.objects.get_for_object(contact_already_opted_out)
        assert versions.count() == 0
