from datetime import datetime
from unittest import mock

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
from datahub.cleanup.query_utils import get_related_fields
from datahub.cleanup.test.commands.factories import ShallowInvestmentProjectFactory
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.exceptions import DataHubException
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.leads.test.factories import BusinessLeadFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.omis.quote.test.factories import QuoteFactory
from datahub.search.apps import get_search_app_by_model, get_search_apps

COMMAND_CLASSES = [
    delete_old_records.Command,
    delete_orphans.Command,
]

FROZEN_TIME = datetime(2018, 6, 1, 2, tzinfo=utc)

"""
For each model in the CONFIG attribute for clean-up management commands:
    - specify the factory class to create an instance
    - specify the list of dependent models as a tuple of:
        - dependent factory class to create an instance
        - dependent field name referencing the main model
    - specify any implicitly-defined related models (e.g. for many-to-many fields) that would be
      deleted even for orphaned records
"""
MAPPINGS = {
    'company.Contact': {
        'factory': ContactFactory,
        'dependent_models': (
            (CompanyInteractionFactory, 'contact'),
            (OrderFactory, 'contact'),
            (QuoteFactory, 'accepted_by'),
            (InvestmentProjectFactory, 'client_contacts'),
        ),
        'implicit_related_models': (),
    },
    'company.Company': {
        'factory': CompanyFactory,
        'dependent_models': (
            (CompanyInteractionFactory, 'company'),
            (ContactFactory, 'company'),
            (ShallowInvestmentProjectFactory, 'intermediate_company'),
            (ShallowInvestmentProjectFactory, 'investor_company'),
            (ShallowInvestmentProjectFactory, 'uk_company'),
            (OrderFactory, 'company'),
            (CompanyFactory, 'global_headquarters'),
            (CompanyFactory, 'parent'),
            (BusinessLeadFactory, 'company'),
        ),
        'implicit_related_models': (),
    },
    'event.Event': {
        'factory': EventFactory,
        'dependent_models': (
            (CompanyInteractionFactory, 'event'),
        ),
        'implicit_related_models': (
            'event.Event_teams',
            'event.Event_related_programmes',
        ),
    },
    'interaction.Interaction': {
        'factory': CompanyInteractionFactory,
        'dependent_models': (),
        'implicit_related_models': (),
    },
}


def _format_iterable(value):
    return ', '.join(str(item) for item in value)


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


@pytest.fixture(
    params=(
        (command_cls, model_name, config)
        for command_cls in COMMAND_CLASSES
        for model_name, config in command_cls.CONFIGS.items()
    ),
    ids=_format_iterable,
)
def cleanup_commands_and_configs(request):
    """Fixture that parametrises tests for each clean-up command configuration."""
    # Instantiate the command class
    yield (request.param[0](), *request.param[1:])


def _format_cleanup_mapping(cleanup_mapping):
    command_cls, model_name, _, _, _, dep_field_name = cleanup_mapping
    return _format_iterable((command_cls, model_name, dep_field_name))


@pytest.fixture(
    params=(
        (
            command_cls,
            model_name,
            config,
            MAPPINGS[model_name],
            dep_factory,
            dep_field_name,
        )
        for command_cls in COMMAND_CLASSES
        for model_name, config in command_cls.CONFIGS.items()
        for dep_factory, dep_field_name in MAPPINGS[model_name]['dependent_models']
    ),
    ids=_format_cleanup_mapping,
)
def cleanup_mapping(request):
    """Fixture that parametrises tests for each clean-up command, model and relationship field."""
    # Instantiate the command class
    yield (request.param[0](), *request.param[1:])


@pytest.mark.parametrize(
    'model_name',
    # Get unique models only – must be in a consistent order for parallelised tests
    sorted(
        {model_name for command_cls in COMMAND_CLASSES for model_name in command_cls.CONFIGS}
    )
)
def test_mappings(model_name):
    """
    Test that `MAPPINGS` includes all the data necessary for covering all the cases.
    This is to avoid missing tests when new fields and models are added or changed.
    """
    model = apps.get_model(model_name)

    try:
        mapping = MAPPINGS[model_name]
    except KeyError:
        pytest.fail(f'Please add test cases for deleting orphaned {model}')

    related_fields = get_related_fields(model)
    expected_related_deps = {(field.field.model, field.field.name) for field in related_fields}
    related_deps_in_mapping = {
        (dep_factory._meta.model, dep_field_name)
        for dep_factory, dep_field_name in mapping['dependent_models']
    }

    missing_dep_mappings = expected_related_deps - related_deps_in_mapping
    if missing_dep_mappings:
        dep_list = [f'{model}.{field}' for model, field in missing_dep_mappings]
        error_msg = (
            f'Please add tests for not deleting {model} when the following '
            f'fields reference it: {", ".join(dep_list)}'
        )
        assert not missing_dep_mappings, error_msg


def create_orphanable_model(factory, config, date_value):
    """
    Creates an orphanable model to use in tests.

    The value of `date_value` would determine if the object is really an orphan or not.
    """
    with freeze_time(date_value):
        return factory(
            **{config.date_field: date_value}
        )


@freeze_time(FROZEN_TIME)
@pytest.mark.django_db
def test_run(cleanup_mapping, track_return_values, setup_es):
    """
    Test that:
        - a record without any objects referencing it but not old enough
            doesn't get deleted
        - a record without any objects referencing it and old gets deleted
        - a record with another object referencing it doesn't get deleted
    """
    command, model_name, config, mapping, dep_factory, dep_field_name = cleanup_mapping
    model_factory = mapping['factory']

    delete_return_value_tracker = track_return_values(QuerySet, 'delete')

    datetime_within_threshold = FROZEN_TIME - config.age_threshold
    datetime_older_than_threshold = datetime_within_threshold - relativedelta(days=1)

    # this orphan should NOT get deleted because not old enough
    create_orphanable_model(model_factory, config, datetime_within_threshold)

    # this orphan should get deleted because old
    create_orphanable_model(model_factory, config, datetime_older_than_threshold)

    # this object should NOT get deleted because it has another object referencing it
    non_orphan = create_orphanable_model(model_factory, config, datetime_older_than_threshold)
    is_m2m = dep_factory._meta.model._meta.get_field(dep_field_name).many_to_many
    dep_factory(
        **{dep_field_name: [non_orphan] if is_m2m else non_orphan},
    )

    # 3 + 1 in case of self-references
    total_model_records = 3 + (1 if dep_factory == model_factory else 0)

    setup_es.indices.refresh()

    model = apps.get_model(model_name)
    search_app = get_search_app_by_model(model)
    doc_type = search_app.name

    assert model.objects.count() == total_model_records
    assert setup_es.count(settings.ES_INDEX, doc_type=doc_type)['count'] == total_model_records

    management.call_command(delete_orphans.Command(), model_name)
    setup_es.indices.refresh()

    # Check that the records have been deleted
    assert model.objects.count() == total_model_records - 1
    assert setup_es.count(settings.ES_INDEX, doc_type=doc_type)['count'] == total_model_records - 1

    # Check which models were actually deleted
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]
    assert deletions_by_model[model._meta.label] == 1
    expected_deleted_models = {model._meta.label} | set(mapping['implicit_related_models'])
    assert set(deletions_by_model.keys()) == expected_deleted_models


@freeze_time(FROZEN_TIME)
@pytest.mark.usefixtures('disconnect_delete_search_signal_receivers')
@pytest.mark.django_db
def test_simulate(cleanup_commands_and_configs, track_return_values, setup_es, caplog):
    """
    Test that if --simulate=True is passed in, the command only simulates the action
    without making any actual changes.
    """
    caplog.set_level('INFO')
    delete_return_value_tracker = track_return_values(QuerySet, 'delete')

    command, model_name, config = cleanup_commands_and_configs

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

    # Check which models were actually deleted
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]
    assert deletions_by_model[model._meta.label] == 3
    expected_deleted_models = {model._meta.label} | set(mapping['implicit_related_models'])
    assert set(deletions_by_model.keys()) == expected_deleted_models

    # Check that nothing has actually been deleted
    assert model.objects.count() == 3
    assert setup_es.count(settings.ES_INDEX, doc_type=search_app.name)['count'] == 3


@freeze_time(FROZEN_TIME)
@pytest.mark.django_db
def test_only_print_queries(cleanup_commands_and_configs, monkeypatch, caplog):
    """
    Test that if --only-print-queries is passed, the SQL query is printed but no deletions or
    simulation occurs.
    """
    caplog.set_level('INFO')
    delete_mock = mock.Mock()
    monkeypatch.setattr(QuerySet, 'delete', delete_mock)

    command, model_name, config = cleanup_commands_and_configs

    mapping = MAPPINGS[model_name]
    model_factory = mapping['factory']
    datetime_older_than_threshold = FROZEN_TIME - config.age_threshold - relativedelta(days=1)

    for _ in range(3):
        create_orphanable_model(model_factory, config, datetime_older_than_threshold)

    management.call_command(command, model_name, only_print_queries=True)

    assert not delete_mock.called
    assert 'SQL:' in caplog.text


@pytest.mark.parametrize('cleanup_command_cls', COMMAND_CLASSES, ids=str)
def test_fails_with_invalid_model(cleanup_command_cls):
    """Test that if an invalid value for model is passed in, the command errors."""
    with pytest.raises(CommandError):
        management.call_command(cleanup_command_cls(), 'invalid')


@freeze_time(FROZEN_TIME)
@mock.patch('datahub.search.deletion.bulk')
@pytest.mark.usefixtures('synchronous_on_commit')
@pytest.mark.django_db
def test_with_es_exception(mocked_bulk):
    """
    Test that if ES returns a 5xx error, the command completes but it also
    raises a DataHubException with details of the error.
    """
    mocked_bulk.return_value = (None, [{'delete': {'status': 500}}])

    command_cls = COMMAND_CLASSES[0]
    model_name = next(iter(command_cls.CONFIGS))
    model_factory = MAPPINGS[model_name]['factory']
    config = command_cls.CONFIGS[model_name]

    datetime_older_than_threshold = FROZEN_TIME - config.age_threshold - relativedelta(days=1)
    create_orphanable_model(model_factory, config, datetime_older_than_threshold)

    with pytest.raises(DataHubException):
        management.call_command(command_cls(), model_name)

    model = apps.get_model(model_name)
    assert model.objects.count() == 0
