import pytest
from django.core.exceptions import NON_FIELD_ERRORS

from datahub.company.admin.adviser_forms import (
    AddAdviserFromSSOForm,
    DUPLICATE_USER_MESSAGE,
    NO_MATCHING_USER_MESSAGE,
)
from datahub.company.test.factories import AdviserFactory
from datahub.oauth.sso_api_client import SSORequestError, SSOUserDoesNotExist


FAKE_SSO_USER_DATA = {
    'email': 'email@email.test',
    'user_id': 'c2c1afce-e45e-4139-9913-88b350f7a546',
    'email_user_id': 'test@id.test',
    'first_name': 'Johnny',
    'last_name': 'Cakeman',
    'related_emails': [],
    'contact_email': 'contact@email.test',
    'groups': [],
    'permitted_applications': [],
    'access_profiles': [],
}


@pytest.mark.usefixtures('mock_get_user_by_email', 'mock_get_user_by_email_user_id')
@pytest.mark.django_db
class TestAddAdviserFromSSOForm:
    """Tests for the add adviser from SSO form."""

    def test_validation_fails_when_no_search_email_entered(self):
        """Test that validation fails if no search email is entered."""
        data = {'search_email': ''}
        form = AddAdviserFromSSOForm(data=data)

        assert form.errors == {
            'search_email': ['This field is required.'],
        }

    @pytest.mark.parametrize(
        'factory_kwargs',
        (
            {'sso_email_user_id': FAKE_SSO_USER_DATA['email_user_id']},
            {'email': FAKE_SSO_USER_DATA['email']},
        ),
    )
    def test_validation_fails_when_adviser_already_exists(
        self,
        factory_kwargs,
        mock_get_user_by_email_user_id,
    ):
        """
        Test that validation fails if there's an existing adviser with the same SSO email user
        ID or email (username).
        """
        mock_get_user_by_email_user_id.return_value = FAKE_SSO_USER_DATA
        AdviserFactory(**factory_kwargs)

        data = {'search_email': 'search-email@test.test'}
        form = AddAdviserFromSSOForm(data=data)

        assert form.errors == {
            NON_FIELD_ERRORS: [DUPLICATE_USER_MESSAGE],
        }

    def test_validation_fails_when_adviser_not_in_sso(
        self,
        mock_get_user_by_email,
        mock_get_user_by_email_user_id,
    ):
        """
        Test that validation fails if there's no matching adviser in Staff SSO.
        """
        mock_get_user_by_email.side_effect = SSOUserDoesNotExist()
        mock_get_user_by_email_user_id.side_effect = SSOUserDoesNotExist()

        data = {'search_email': 'search-email@test.test'}
        form = AddAdviserFromSSOForm(data=data)

        assert form.errors == {
            NON_FIELD_ERRORS: [NO_MATCHING_USER_MESSAGE],
        }

    def test_validation_fails_when_there_is_a_request_error(self, mock_get_user_by_email_user_id):
        """
        Test that validation fails if there's an error communicating with Staff SSO.
        """
        mock_get_user_by_email_user_id.side_effect = SSORequestError('Test error')

        data = {'search_email': 'search-email@test.test'}
        form = AddAdviserFromSSOForm(data=data)

        assert form.errors == {
            NON_FIELD_ERRORS: [
                'There was an error communicating with Staff SSO: Test error. Please try again.',
            ],
        }

    def test_can_create_an_adviser_by_email_user_id(self, mock_get_user_by_email_user_id):
        """Test that an adviser can be created using its SSO email user ID."""
        mock_get_user_by_email_user_id.return_value = FAKE_SSO_USER_DATA

        data = {'search_email': 'search-email@test.test'}
        form = AddAdviserFromSSOForm(data=data)

        assert not form.errors

        adviser = form.save()

        assert adviser.email == FAKE_SSO_USER_DATA['email']
        assert adviser.sso_email_user_id == FAKE_SSO_USER_DATA['email_user_id']
        assert adviser.contact_email == FAKE_SSO_USER_DATA['contact_email']
        assert adviser.first_name == FAKE_SSO_USER_DATA['first_name']
        assert adviser.last_name == FAKE_SSO_USER_DATA['last_name']

    def test_can_create_an_adviser_by_email(
        self,
        mock_get_user_by_email_user_id,
        mock_get_user_by_email,
    ):
        """
        Test that an adviser can be created using its SSO email (when there is no match on
        email user ID).
        """
        mock_get_user_by_email_user_id.side_effect = SSOUserDoesNotExist()
        mock_get_user_by_email.return_value = FAKE_SSO_USER_DATA

        data = {'search_email': 'search-email@test.test'}
        form = AddAdviserFromSSOForm(data=data)

        assert not form.errors

        adviser = form.save()

        assert adviser.email == FAKE_SSO_USER_DATA['email']
        assert adviser.sso_email_user_id == FAKE_SSO_USER_DATA['email_user_id']
        assert adviser.contact_email == FAKE_SSO_USER_DATA['contact_email']
        assert adviser.first_name == FAKE_SSO_USER_DATA['first_name']
        assert adviser.last_name == FAKE_SSO_USER_DATA['last_name']
