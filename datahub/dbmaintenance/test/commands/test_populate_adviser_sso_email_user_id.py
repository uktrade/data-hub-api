from unittest.mock import Mock

import pytest
from django.core.management import call_command

from datahub.company.test.factories import AdviserFactory
from datahub.dbmaintenance.management.commands import populate_adviser_sso_email_user_id
from datahub.oauth.sso_api_client import SSORequestError, SSOUserDoesNotExist
from datahub.search.investment.signals import investment_project_sync_es_adviser_change


FAKE_SSO_USER_DATA = {
    'email': 'EMAil@email.test',
    'user_id': 'c2c1afce-e45e-4139-9913-88b350f7a546',
    'email_user_id': 'id@id.test',
    'first_name': 'Johnny',
    'last_name': 'Cakeman',
    'related_emails': [],
    'contact_email': 'contact@email.test',
    'groups': [],
    'permitted_applications': [],
    'access_profiles': [],
}


@pytest.mark.django_db
class TestPopulateAdviserSSOEmailUserIDCommand:
    """Tests for the populate_adviser_sso_email_user_id management command."""

    @pytest.mark.parametrize(
        'adviser_factory,get_user_by_email_mock,expected_sso_email_user_id,expected_log_messages',
        (
            # If sso_email_user_id is None and SSO returns a user with a matching
            # primary email (ignoring case), sso_email_user_id should be updated
            pytest.param(
                lambda: AdviserFactory(email='Email@email.test', sso_email_user_id=None),
                Mock(return_value=FAKE_SSO_USER_DATA),
                FAKE_SSO_USER_DATA['email_user_id'],
                ['1 advisers updated', '0 advisers skipped', '0 advisers with errors'],
                id='match-with-matching-email',
            ),
            # If sso_email_user_id is None and SSO returns a user with a non-matching
            # primary email, sso_email_user_id should be unchanged
            pytest.param(
                lambda: AdviserFactory(email='alternative@email.test', sso_email_user_id=None),
                Mock(return_value=FAKE_SSO_USER_DATA),
                None,
                ['0 advisers updated', '1 advisers skipped', '0 advisers with errors'],
                id='match-with-unmatching-email',
            ),
            # If sso_email_user_id is None and there is no matching user in SSO,
            # sso_email_user_id should be unchanged
            pytest.param(
                lambda: AdviserFactory(email='alternative@email.test', sso_email_user_id=None),
                Mock(side_effect=SSOUserDoesNotExist()),
                None,
                ['0 advisers updated', '1 advisers skipped', '0 advisers with errors'],
                id='no-match',
            ),
            # If sso_email_user_id is None and the user is inactive, no change should
            # be attempted
            pytest.param(
                lambda: AdviserFactory(
                    email='email@email.test',
                    sso_email_user_id=None,
                    is_active=False,
                ),
                Mock(return_value=FAKE_SSO_USER_DATA),
                None,
                ['0 advisers updated', '0 advisers skipped', '0 advisers with errors'],
                id='adviser-is-inactive',
            ),
            # If sso_email_user_id is not None, no change should be attempted
            pytest.param(
                lambda: AdviserFactory(
                    email='email@email.test',
                    sso_email_user_id='existing@id.test',
                ),
                Mock(return_value=FAKE_SSO_USER_DATA),
                'existing@id.test',
                ['0 advisers updated', '0 advisers skipped', '0 advisers with errors'],
                id='adviser-already-has-sso-email-user-id',
            ),
            # If sso_email_user_id is None and there is a request error,
            # sso_email_user_id should be unchanged but the exception should
            # not be propagated
            pytest.param(
                lambda: AdviserFactory(email='bad_email_address', sso_email_user_id=None),
                Mock(side_effect=SSORequestError('Bad request')),
                None,
                ['0 advisers updated', '0 advisers skipped', '1 advisers with errors'],
                id='no-match',
            ),
        ),
    )
    def test_updates_sso_email_user_if_appropriate(
        self,
        adviser_factory,
        get_user_by_email_mock,
        expected_sso_email_user_id,
        expected_log_messages,
        monkeypatch,
        caplog,
    ):
        """Test adviser SSO email user ID updating in various different cases."""
        caplog.set_level('INFO')

        monkeypatch.setattr(
            populate_adviser_sso_email_user_id,
            'get_user_by_email',
            get_user_by_email_mock,
        )

        adviser = adviser_factory()

        command = populate_adviser_sso_email_user_id.Command()
        call_command(command)

        adviser.refresh_from_db()

        assert adviser.sso_email_user_id == expected_sso_email_user_id

        for message in expected_log_messages:
            assert message in caplog.text

    def test_simulate_does_not_save_changes(self, monkeypatch, caplog):
        """Test that simulate does not save model object changes."""
        caplog.set_level('INFO')

        monkeypatch.setattr(
            populate_adviser_sso_email_user_id,
            'get_user_by_email',
            Mock(return_value=FAKE_SSO_USER_DATA),
        )

        adviser = AdviserFactory(email='email@email.test', sso_email_user_id=None)

        command = populate_adviser_sso_email_user_id.Command()
        call_command(command, simulate=True)

        adviser.refresh_from_db()

        assert not adviser.sso_email_user_id
        assert '1 advisers updated' in caplog.text

    def test_does_not_resync_search_investment_project_documents(self, monkeypatch):
        """
        Test that investment projects are not resynced to Elasticsearch when an adviser is
        updated.

        This is due to the use of the disable_search_signal_receivers decorator.
        """
        monkeypatch.setattr(
            populate_adviser_sso_email_user_id,
            'get_user_by_email',
            Mock(return_value=FAKE_SSO_USER_DATA),
        )

        investment_project_sync_es_adviser_change_mock = Mock(
            wraps=investment_project_sync_es_adviser_change,
        )
        monkeypatch.setattr(
            'datahub.search.investment.signals.investment_project_sync_es_adviser_change',
            investment_project_sync_es_adviser_change_mock,
        )

        adviser = AdviserFactory(email='email@email.test', sso_email_user_id=None)

        command = populate_adviser_sso_email_user_id.Command()
        call_command(command)

        adviser.refresh_from_db()

        assert adviser.sso_email_user_id == FAKE_SSO_USER_DATA['email_user_id']
        assert not investment_project_sync_es_adviser_change_mock.called
