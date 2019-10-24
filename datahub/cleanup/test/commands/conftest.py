import pytest
from django.db.models.signals import post_delete

from datahub.search.apps import get_search_apps


@pytest.fixture
def disconnect_delete_search_signal_receivers(es_with_signals):
    """
    Fixture that disables signal receivers that delete documents in Elasticsearch.

    This is used in tests targeting rollback behaviour. This is because search tests typically
    use the synchronous_on_commit fixture, which doesn't model rollback behaviour correctly.

    The signal receivers to disable are determined by checking the signal connected to and the
    model observed.
    """
    disconnected_signal_receivers = []

    search_apps = get_search_apps()
    for search_app in search_apps:
        app_db_model = search_app.queryset.model
        for receiver in search_app.get_signal_receivers():
            if receiver.signal is post_delete and receiver.sender is app_db_model:
                receiver.disconnect()
                disconnected_signal_receivers.append(receiver)

    yield

    # We reconnect the receivers for completeness, though in theory it's not necessary as
    # es_with_signals will disconnect them anyway

    for receiver in disconnected_signal_receivers:
        receiver.connect()
