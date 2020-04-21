from datetime import datetime
from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.core import management
from django.db.models import QuerySet
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.cleanup.management.commands import delete_orphans
from datahub.cleanup.query_utils import get_relations_to_delete
from datahub.cleanup.test.commands.factories import ShallowInvestmentProjectFactory
from datahub.company.test.factories import (
    CompanyFactory,
    ContactFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.core.exceptions import DataHubException
from datahub.core.model_helpers import get_related_fields
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.test.factories import (
    OrderFactory,
)
from datahub.omis.quote.test.factories import QuoteFactory
from datahub.search.apps import get_search_app_by_model

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
            (CompanyReferralFactory, 'contact'),
            (CompanyInteractionFactory, 'contacts'),
            (OrderFactory, 'contact'),
            (QuoteFactory, 'accepted_by'),
            (InvestmentProjectFactory, 'client_contacts'),
        ),
        'implicit_related_models': (),
        'ignored_models': (),
    },
    'company.Company': {
        'factory': CompanyFactory,
        'dependent_models': (
            (CompanyReferralFactory, 'company'),
            (CompanyInteractionFactory, 'company'),
            (ContactFactory, 'company'),
            (ShallowInvestmentProjectFactory, 'intermediate_company'),
            (ShallowInvestmentProjectFactory, 'investor_company'),
            (ShallowInvestmentProjectFactory, 'uk_company'),
            (OrderFactory, 'company'),
            (CompanyFactory, 'transferred_to'),
            (CompanyFactory, 'global_headquarters'),
            (OneListCoreTeamMemberFactory, 'company'),
            (LargeCapitalInvestorProfileFactory, 'investor_company'),
        ),
        'implicit_related_models': (),
        'ignored_models': (),
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
        'ignored_models': (),
    },
}


def _format_iterable(value):
    return ', '.join(str(item) for item in value)


@pytest.fixture(
    params=(
        (model_name, config)
        for model_name, config in delete_orphans.Command.CONFIGS.items()
    ),
    ids=_format_iterable,
)
def cleanup_configs(request):
    """Fixture that parametrises tests for each clean-up command configuration."""
    # Instantiate the command class
    yield request.param


@pytest.mark.parametrize('model_name,config', delete_orphans.Command.CONFIGS.items())
def test_mappings(model_name, config):
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
    expected_related_deps = {
        (field.field.model, field.field.name)
        for field in related_fields
        if field not in config.excluded_relations
    }
    related_deps_in_mapping = {
        (dep_factory._meta.model, dep_field_name)
        for dep_factory, dep_field_name in mapping['dependent_models']
    }
    ignored_relations = {
        (apps.get_model(model_label), field_name)
        for model_label, field_name in mapping['ignored_models']
    }

    missing_dep_mappings = expected_related_deps - related_deps_in_mapping - ignored_relations
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
            **{config.date_field: date_value},
        )


@pytest.mark.parametrize('model_name,config', delete_orphans.Command.CONFIGS.items())
def test_configs(model_name, config):
    """
    Test that configs for delete_orphans only specify a single filter, and do not specify any
    relation filters.

    These are not allowed as they are not currently needed for delete_orphans, and would
    complicate the tests.
    """
    assert len(config.filters) == 1, (
        f'Exactly one filter must be specified for the delete_orphans config for model '
        f'{model_name}',
    )

    assert not config.relation_filter_mapping, (
        f'Relation filters cannot be used for delete_orphan configs (one detected for the '
        f'{model_name} config)',
    )


@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize(
    'model_name,config,mapping,dep_factory,dep_field_name',
    (
        (
            model_name,
            config,
            MAPPINGS[model_name],
            dep_factory,
            dep_field_name,
        )
        for model_name, config in delete_orphans.Command.CONFIGS.items()
        for dep_factory, dep_field_name in MAPPINGS[model_name]['dependent_models']
    ),
)
@pytest.mark.django_db
def test_run(
    model_name,
    config,
    mapping,
    dep_factory,
    dep_field_name,
    track_return_values,
    es_with_signals,
    es_collector_context_manager,
):
    """
    Test that:
        - a record without any objects referencing it but not old enough
            doesn't get deleted
        - a record without any objects referencing it and old gets deleted
        - a record with another object referencing it doesn't get deleted
    """
    # Set up the state before running the command
    command = delete_orphans.Command()
    model_factory = mapping['factory']
    filter_config = config.filters[0]

    delete_return_value_tracker = track_return_values(QuerySet, 'delete')

    datetime_within_threshold = filter_config.cut_off_date
    datetime_older_than_threshold = filter_config.cut_off_date - relativedelta(days=1)

    with es_collector_context_manager as collector:
        # this orphan should NOT get deleted because not old enough
        create_orphanable_model(model_factory, filter_config, datetime_within_threshold)

        # this orphan should get deleted because old
        create_orphanable_model(model_factory, filter_config, datetime_older_than_threshold)

        # this object should NOT get deleted because it has another object referencing it
        non_orphan = create_orphanable_model(
            model_factory,
            filter_config,
            datetime_older_than_threshold,
        )
        is_m2m = dep_factory._meta.model._meta.get_field(dep_field_name).many_to_many
        dep_factory(
            **{dep_field_name: [non_orphan] if is_m2m else non_orphan},
        )

        collector.flush_and_refresh()

    # 3 + 1 in case of self-references
    total_model_records = 3 + (1 if dep_factory == model_factory else 0)

    model = apps.get_model(model_name)
    search_app = get_search_app_by_model(model)
    read_alias = search_app.es_model.get_read_alias()

    assert model.objects.count() == total_model_records
    assert es_with_signals.count(read_alias)['count'] == total_model_records

    # Run the command
    management.call_command(command, model_name)
    es_with_signals.indices.refresh()

    # Check that the records have been deleted
    assert model.objects.count() == total_model_records - 1
    assert es_with_signals.count(read_alias)['count'] == total_model_records - 1

    # Check which models were actually deleted
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]
    assert deletions_by_model[model._meta.label] == 1
    expected_deleted_models = {model._meta.label} | set(mapping['implicit_related_models'])
    actual_deleted_models = {  # only include models actually deleted
        deleted_model
        for deleted_model, deleted_count in deletions_by_model.items()
        if deleted_count
    }
    assert actual_deleted_models == expected_deleted_models


@freeze_time(FROZEN_TIME)
@pytest.mark.usefixtures('disconnect_delete_search_signal_receivers')
@pytest.mark.django_db
def test_simulate(
    cleanup_configs,
    track_return_values,
    es_with_signals,
    es_collector_context_manager,
):
    """
    Test that if --simulate is passed in, the command only simulates the action
    without making any actual changes.
    """
    # Set up the state before running the command
    delete_return_value_tracker = track_return_values(QuerySet, 'delete')
    model_name, config = cleanup_configs
    filter_config = config.filters[0]
    command = delete_orphans.Command()
    mapping = MAPPINGS[model_name]
    model_factory = mapping['factory']
    datetime_older_than_threshold = filter_config.cut_off_date - relativedelta(days=1)

    with es_collector_context_manager as collector:
        for _ in range(3):
            create_orphanable_model(model_factory, filter_config, datetime_older_than_threshold)

        collector.flush_and_refresh()

    model = apps.get_model(model_name)
    search_app = get_search_app_by_model(model)
    read_alias = search_app.es_model.get_read_alias()

    assert model.objects.count() == 3
    assert es_with_signals.count(read_alias)['count'] == 3

    # Run the command
    management.call_command(command, model_name, simulate=True)
    es_with_signals.indices.refresh()

    # Check which models were actually deleted
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]
    expected_deleted_models = {model._meta.label} | set(mapping['implicit_related_models'])
    actual_deleted_models = {  # only include models actually deleted
        deleted_model
        for deleted_model, deleted_count in deletions_by_model.items()
        if deleted_count
    }
    assert actual_deleted_models == expected_deleted_models
    assert deletions_by_model[model._meta.label] == 3

    # Check that nothing has actually been deleted
    assert model.objects.count() == 3
    assert es_with_signals.count(read_alias)['count'] == 3


@freeze_time(FROZEN_TIME)
@pytest.mark.django_db
def test_only_print_queries(cleanup_configs, monkeypatch, caplog):
    """
    Test that if --only-print-queries is passed, the SQL query is printed but no deletions or
    simulation occurs.
    """
    caplog.set_level('INFO')
    delete_mock = mock.Mock()
    monkeypatch.setattr(QuerySet, 'delete', delete_mock)

    model_name, config = cleanup_configs
    filter_config = config.filters[0]
    command = delete_orphans.Command()

    model = apps.get_model(model_name)
    mapping = MAPPINGS[model_name]
    model_factory = mapping['factory']
    datetime_older_than_threshold = filter_config.cut_off_date - relativedelta(days=1)

    for _ in range(3):
        create_orphanable_model(model_factory, filter_config, datetime_older_than_threshold)

    management.call_command(command, model_name, only_print_queries=True)

    assert not delete_mock.called

    log_text = caplog.text.lower()
    assert f'{model._meta.verbose_name_plural} to delete:' in log_text

    for relation in get_relations_to_delete(model):
        related_meta = relation.related_model._meta
        expected_related_log = (
            f'{related_meta.verbose_name_plural} to delete '
            f'(via {related_meta.model_name}.{relation.remote_field.name}): '
        ).lower()
        assert expected_related_log in log_text
        assert f'from "{related_meta.db_table}"' in log_text


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

    command = delete_orphans.Command()
    model_name = next(iter(delete_orphans.Command.CONFIGS))
    model_factory = MAPPINGS[model_name]['factory']
    filter_config = delete_orphans.Command.CONFIGS[model_name].filters[0]

    datetime_older_than_threshold = (
        FROZEN_TIME
        - filter_config.age_threshold
        - relativedelta(days=1)
    )
    create_orphanable_model(model_factory, filter_config, datetime_older_than_threshold)

    with pytest.raises(DataHubException):
        management.call_command(command, model_name)

    model = apps.get_model(model_name)
    assert model.objects.count() == 0
