import io

import pytest
from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.test import Client
from django.urls import reverse
from rest_framework import status

from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction.admin_csv_import import INTERACTION_IMPORTER_FEATURE_FLAG_NAME
from datahub.interaction.models import Interaction, InteractionPermission


@pytest.fixture()
def interaction_importer_feature_flag():
    """Creates the import interactions tool feature flag."""
    yield FeatureFlagFactory(code=INTERACTION_IMPORTER_FEATURE_FLAG_NAME)


import_interactions_url = reverse(
    admin_urlname(Interaction._meta, 'import'),
)
interaction_change_list_url = reverse(
    admin_urlname(Interaction._meta, 'changelist'),
)


class TestInteractionAdminChangeList(AdminTestMixin):
    """Tests for the contact admin change list."""

    def test_load_import_link_exists(self, interaction_importer_feature_flag):
        """
        Test that there is a link to import interactions on the interaction change list page.
        """
        response = self.client.get(interaction_change_list_url)
        assert response.status_code == status.HTTP_200_OK

        assert import_interactions_url in response.rendered_content

    def test_import_link_does_not_exist_if_only_has_view_permission(self):
        """
        Test that there is not a link to import interactions if the user only has the delete
        (but not change) permission for interactions.
        """
        user = create_test_user(
            permission_codenames=(InteractionPermission.view_all,),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(interaction_change_list_url)
        assert response.status_code == status.HTTP_200_OK

        assert f'Select {Interaction._meta.verbose_name} to view' in response.rendered_content
        assert import_interactions_url not in response.rendered_content

    def test_import_link_does_not_exist_if_feature_flag_inactive(self):
        """
        Test that there is not a link to import interactions if the feature flag is inactive.
        """
        response = self.client.get(interaction_change_list_url)
        assert response.status_code == status.HTTP_200_OK

        assert import_interactions_url not in response.rendered_content


class TestImportInteractionsSelectFileView(AdminTestMixin):
    """Tests for the import interaction select file form."""

    def test_redirects_to_login_page_if_not_logged_in(self, interaction_importer_feature_flag):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        client = Client()
        response = client.get(import_interactions_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == self.login_url_with_redirect(
            import_interactions_url,
        )

    def test_redirects_to_login_page_if_not_staff(self, interaction_importer_feature_flag):
        """Test that the view redirects to the login page if the user isn't a member of staff."""
        user = create_test_user(is_staff=False, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(import_interactions_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == self.login_url_with_redirect(
            import_interactions_url,
        )

    def test_permission_denied_if_staff_and_without_change_permission(
        self,
        interaction_importer_feature_flag,
    ):
        """
        Test that the view returns a 403 response if the staff user does not have the
        change interaction permission.
        """
        user = create_test_user(
            permission_codenames=(InteractionPermission.view_all,),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(import_interactions_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_displays_page_if_with_correct_permissions(self, interaction_importer_feature_flag):
        """
        Test that the view returns displays the form if the feature flag is active
        and the user has the correct permissions.
        """
        response = self.client.get(import_interactions_url)

        assert response.status_code == status.HTTP_200_OK
        assert 'form' in response.context

    def test_does_not_allow_file_without_correct_columns(
        self,
        interaction_importer_feature_flag,
    ):
        """Test that the form rejects a CSV file that doesn't have the required columns."""
        file = io.BytesIO(b'test\r\nrow')
        file.name = 'test.csv'

        response = self.client.post(
            import_interactions_url,
            data={
                'csv_file': file,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']

        assert 'csv_file' in form.errors
        assert form.errors['csv_file'] == [
            'This file is missing the following required columns: '
            'adviser_1, contact_email, date, kind, service.',
        ]

    def test_rejects_large_files(self, interaction_importer_feature_flag):
        """
        Test that large files are rejected.

        Note: INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE is set to 1024 in config.settings.test
        """
        file_size = settings.INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE + 1
        file = io.BytesIO(b'-' * file_size)
        file.name = 'test.csv'

        response = self.client.post(
            import_interactions_url,
            data={
                'csv_file': file,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert messages[0].level == django_messages.ERROR
        assert messages[0].message == (
            'The file test.csv was too large. Files must be less than 1.0 KB.'
        )

    def test_redirects_on_valid_file(self, interaction_importer_feature_flag):
        """
        Test that accepts_dit_email_marketing is updated for the contacts specified in the CSV
        file.
        """
        filename = 'filea.csv'
        file = io.BytesIO("""kind,date,adviser_1,contact_email,service\r
interaction,01/01/2018,John Dreary,person@company,Account Management
""".encode(encoding='utf-8'))
        file.name = filename

        response = self.client.post(
            import_interactions_url,
            follow=True,
            data={
                'csv_file': file,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == interaction_change_list_url

    @pytest.mark.parametrize('http_method', ('get', 'post'))
    def test_returns_404_if_feature_flag_inactive(self, http_method):
        """Test that the a 404 is returned if the feature flag is inactive."""
        response = self.client.generic(
            http_method,
            import_interactions_url,
            data={},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
