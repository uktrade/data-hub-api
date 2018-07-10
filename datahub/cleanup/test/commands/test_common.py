from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.core import management
from django.core.management import CommandError
from django.db.models import QuerySet
from django.db.models.signals import post_delete
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.cleanup.management.commands import delete_old_records, delete_orphans
from datahub.cleanup.test.commands.test_delete_orphans import create_orphanable_model, MAPPINGS
from datahub.search.apps import get_search_app_by_model, get_search_apps

COMMAND_CLASSES = [
    delete_old_records.Command,
    delete_orphans.Command,
]

FROZEN_TIME = datetime(2018, 6, 1, 2, tzinfo=utc)


@pytest.fixture
def disconnect_delete_search_signal_receivers(setup_es):
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
        for receiver in search_app.get_signals_receivers():
            if receiver.signal is post_delete and receiver.sender is app_db_model:
                receiver.disconnect()
                disconnected_signal_receivers.append(receiver)

    yield

    # We reconnect the receivers for completeness, though in theory it's not necessary as setup_es
    # will disconnect them anyway

    for receiver in disconnected_signal_receivers:
        receiver.connect()


@pytest.fixture(params=(
    (command_cls(), model_name, config)
    for command_cls in COMMAND_CLASSES
    for model_name, config in command_cls.CONFIGS.items()
), ids=str)
def cleanup_args(request):
    """Fixture that parametrises tests for each clean-up command configuration."""
    yield request.param


@freeze_time(FROZEN_TIME)
@pytest.mark.usefixtures('disconnect_delete_search_signal_receivers')
@pytest.mark.django_db
def test_simulate(cleanup_args, track_return_values, setup_es, caplog):
    """
    Test that if --simulate=True is passed in, the command only simulates the action
    without making any actual changes.
    """
    caplog.set_level('INFO')
    delete_return_value_tracker = track_return_values(QuerySet, 'delete')

    command, model_name, config = cleanup_args

    mapping = MAPPINGS[model_name]
    model_factory = mapping['factory']
    datetime_older_than_threshold = FROZEN_TIME - config.age_threshold - relativedelta(days=1)

    for _ in range(3):
        create_orphanable_model(model_factory, config, datetime_older_than_threshold)

    setup_es.indices.refresh()

    model = apps.get_model(model_name)
    search_app = get_search_app_by_model(model)

    assert model.objects.count() == 3
    assert setup_es.count(settings.ES_INDEX, doc_type=search_app.name)['count'] == 3
    management.call_command(command, model_name, simulate=True)

    setup_es.indices.refresh()

    # Check that 3 records would have been deleted
    assert 'to delete: 3' in caplog.text
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]
    assert deletions_by_model[model._meta.label] == 3

    # Check that nothing has actually been deleted
    assert model.objects.count() == 3
    assert setup_es.count(settings.ES_INDEX, doc_type=search_app.name)['count'] == 3


@pytest.mark.parametrize('cleanup_command_cls', COMMAND_CLASSES, ids=str)
def test_fails_with_invalid_model(cleanup_command_cls):
    """Test that if an invalid value for model is passed in, the command errors."""
    with pytest.raises(CommandError):
        management.call_command(cleanup_command_cls(), 'invalid')
