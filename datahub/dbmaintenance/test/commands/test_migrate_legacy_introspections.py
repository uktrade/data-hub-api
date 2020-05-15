from datetime import datetime
from unittest.mock import Mock

import factory
import pytest
from django.core.management import call_command
from django.utils.timezone import utc
from freezegun import freeze_time
from oauth2_provider.models import AccessToken

from datahub.company.test.factories import AdviserFactory
from datahub.dbmaintenance.management.commands import migrate_legacy_introspections
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.models import UserEvent


class AccessTokenFactory(factory.django.DjangoModelFactory):
    """AccessToken factory."""

    user = factory.SubFactory(AdviserFactory)
    token = factory.Faker('password', length=20)
    expires = factory.Faker(
        'date_time_between',
        end_date=datetime(2020, 5, 10, tzinfo=utc),
        tzinfo=utc,
    )
    scope = 'read write data-hub:internal-front-end'

    class Meta:
        model = AccessToken


@pytest.mark.django_db
class TestMigrateLegacyIntrospectionsCommand:
    """Tests for the migrate_legacy_introspections command."""

    @pytest.mark.parametrize(
        'token_scope',
        (
            'read write data-hub:internal-front-end',
            'read write introspection data-hub:internal-front-end',
        ),
    )
    def test_migrates_legacy_access_tokens(self, token_scope):
        """A user event should be created with the correct values for a matching access token."""
        with freeze_time('2020-02-03 12:25:54'):
            token = AccessTokenFactory(scope=token_scope)

        command = migrate_legacy_introspections.Command()
        call_command(command)

        events = UserEvent.objects.all()
        # Uses len() to force evaluation
        assert len(events) == 1

        event = events.first()
        assert event.adviser == token.user
        assert event.timestamp == token.created
        assert event.type == UserEventType.OAUTH_TOKEN_INTROSPECTION
        assert event.data == {'source': 'legacy_access_token'}

    def test_processes_multiple_batches(self):
        """Test that multiple batches are processed as expected."""
        batch_size = 5
        # Set to 7 so that the second batch is incomplete
        num_objects = 7
        tokens = AccessTokenFactory.create_batch(num_objects)

        command = migrate_legacy_introspections.Command()
        call_command(command, batch_size=batch_size)

        event_adviser_ids = UserEvent.objects.values_list('adviser_id', flat=True)
        # Uses len() to force evaluation
        assert len(event_adviser_ids) == num_objects

        token_user_ids = {token.user_id for token in tokens}
        assert set(event_adviser_ids) == token_user_ids

    def test_rolls_back_on_error(self, monkeypatch):
        """All changes should be rolled back if there is an error."""
        logger_info_mock = Mock(side_effect=[None, ValueError()])
        monkeypatch.setattr(migrate_legacy_introspections.logger, 'info', logger_info_mock)

        batch_size = 5
        num_objects = 7
        AccessTokenFactory.create_batch(num_objects)

        command = migrate_legacy_introspections.Command()
        with pytest.raises(ValueError):
            call_command(command, batch_size=batch_size)

        assert not UserEvent.objects.exists()

    @pytest.mark.parametrize(
        'factory_kwargs',
        (
            {'user': None},
            {'expires': datetime(2020, 5, 10, 1, tzinfo=utc)},
            {'scope': ''},
        ),
    )
    def test_ignores_irrelevant_tokens(self, factory_kwargs):
        """Irrelevant access tokens should be ignored."""
        with freeze_time('2020-02-03 12:25:54'):
            AccessTokenFactory(**factory_kwargs)

        command = migrate_legacy_introspections.Command()
        call_command(command)

        assert not UserEvent.objects.exists()
