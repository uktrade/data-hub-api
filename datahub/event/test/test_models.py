from django.conf import settings

from datahub.event.test.factories import EventFactory


def test_event_get_absolute_url():
    """Test that Event.get_absolute_url() returns the correct URL."""
    event = EventFactory.build()
    assert event.get_absolute_url() == (
        f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["event"]}/{event.pk}'
    )
