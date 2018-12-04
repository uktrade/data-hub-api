from datetime import datetime
from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.core import management
from django.db.models import QuerySet
from django.utils.timezone import utc
from freezegun import freeze_time


from datahub.cleanup.management.commands import delete_old_records
from datahub.cleanup.management.commands.delete_old_records import (
    INTERACTION_EXPIRY_PERIOD,
    ORDER_EXPIRY_PERIOD,
    ORDER_MODIFIED_ON_CUT_OFF,
)
from datahub.cleanup.query_utils import get_relations_to_delete
from datahub.core.exceptions import DataHubException
from datahub.core.model_helpers import get_related_fields
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.omis.payment.test.factories import (
    ApprovedRefundFactory,
    PaymentFactory,
    PaymentGatewaySessionFactory,
)
from datahub.search.apps import get_search_app_by_model


FROZEN_TIME = datetime(2018, 6, 1, 2, tzinfo=utc)


INTERACTION_DELETE_BEFORE_DATETIME = FROZEN_TIME - INTERACTION_EXPIRY_PERIOD
ORDER_DELETE_BEFORE_DATETIME = FROZEN_TIME - ORDER_EXPIRY_PERIOD


MAPPING = {
    'interaction.Interaction': {
        'factory': CompanyInteractionFactory,
        'implicitly_deletable_models': set(),
        'expired_object_kwargs': {
            'date': INTERACTION_DELETE_BEFORE_DATETIME - relativedelta(days=1),
        },
        'unexpired_objects_kwargs': [
            {
                'date': INTERACTION_DELETE_BEFORE_DATETIME,
            },
        ],
        'relations': [],
    },
    'order.Order': {
        'factory': OrderFactory,
        'implicitly_deletable_models': {
            'order.Order_service_types',
            'order.OrderAssignee',
            'order.OrderSubscriber',
            'omis-payment.Payment',
            'omis-payment.Refund',
            'omis-payment.PaymentGatewaySession',
        },
        'expired_object_kwargs': {
            'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
            'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
        },
        'unexpired_objects_kwargs': [
            {
                'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                'modified_on': ORDER_MODIFIED_ON_CUT_OFF,
            },
            {
                'created_on': ORDER_DELETE_BEFORE_DATETIME,
                'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
            },
            {
                'created_on': ORDER_DELETE_BEFORE_DATETIME,
                'modified_on': ORDER_MODIFIED_ON_CUT_OFF,
            },
        ],
        'relations': [
            {
                'factory': PaymentFactory,
                'field': 'order',
                'expired_objects_kwargs': [
                    {
                        'received_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                    },
                ],
                'unexpired_objects_kwargs': [
                    {
                        'received_on': ORDER_DELETE_BEFORE_DATETIME,
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                    },
                    {
                        'received_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF,
                    },
                ],
            },
            {
                'factory': ApprovedRefundFactory,
                'field': 'order',
                'expired_objects_kwargs': [
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                        'level2_approved_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                    },
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                    },
                ],
                'unexpired_objects_kwargs': [
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME,
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                        'level2_approved_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                    },
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF,
                        'level2_approved_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                    },
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                        'level2_approved_on': ORDER_DELETE_BEFORE_DATETIME,
                    },
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF,
                        'level2_approved_on': None,
                    },
                    {
                        'created_on': ORDER_DELETE_BEFORE_DATETIME,
                        'modified_on': ORDER_MODIFIED_ON_CUT_OFF - relativedelta(days=1),
                        'level2_approved_on': None,
                    },
                ],
            },
            {
                'factory': PaymentGatewaySessionFactory,
                'field': 'order',
                'expired_objects_kwargs': [
                    {
                        'modified_on': ORDER_DELETE_BEFORE_DATETIME - relativedelta(days=1),
                    },
                ],
                'unexpired_objects_kwargs': [
                    {
                        'modified_on': ORDER_DELETE_BEFORE_DATETIME,
                    },
                ],
            },
        ],
    },
}


@pytest.mark.parametrize(
    'model_label,config',
    delete_old_records.Command.CONFIGS.items(),
)
def test_mappings(model_label, config):
    """
    Test that `MAPPING` includes all the data necessary for covering all the cases.
    This is to avoid missing tests when new the configurations for delete_old_records are changed.
    """
    assert model_label in MAPPING, (
        f'No test cases for deleting old records for model {model_label} specified in MAPPING'
    )

    if config.relation_filter_mapping:
        mapping = MAPPING[model_label]
        related_models_in_config = {field.field.model for field in config.relation_filter_mapping}
        related_models_in_mapping = {
            relation['factory']._meta.get_model_class()
            for relation in mapping['relations']
        }
        assert related_models_in_config == related_models_in_mapping, (
            'Missing test cases for relation filters for model  {model_label} detected'
        )


@pytest.mark.parametrize('model_label,config', delete_old_records.Command.CONFIGS.items())
def test_configs(model_label, config):
    """
    Test that configs for delete_old_records cover all relations for the model.

    This is to make sure any new relations that are added are not missed from the
    configurations.
    """
    model = apps.get_model(model_label)
    related_fields = get_related_fields(model)

    field_missing_from_config = (
        set(related_fields)
        - (config.relation_filter_mapping or {}).keys()
        - set(config.excluded_relations)
    )
    fields_for_error_message = [_format_field(field) for field in field_missing_from_config]
    assert not field_missing_from_config, (
        f'The following related fields are missing from the config for {model_label}: '
        f'{fields_for_error_message}. Please add them to the ModelCleanupConfig in either '
        f'relation_filter_mapping or excluded_relations.\n'
        f'\n'
        f'Only add the model to excluded_relations if its existence should not affect '
        f'whether {model_label} objects are be deleted. You can specify an empty filter '
        f'list in relation_filter_mapping if they should not be filtered.\n'
        f'\n'
        f'See ModelCleanupConfig and the delete_old_records command for more details.'
    )


def _generate_run_args():
    """Flattens MAPPING so it can be used to parametrise the test_run() test."""
    for model_label, mapping in MAPPING.items():
        expired_object_kwargs = mapping['expired_object_kwargs']

        yield model_label, expired_object_kwargs, None, None, True

        for kwargs in mapping['unexpired_objects_kwargs']:
            yield model_label, kwargs, None, None, False

        for relation_mapping in mapping['relations']:
            for relation_kwargs in relation_mapping['expired_objects_kwargs']:
                yield model_label, expired_object_kwargs, relation_mapping, relation_kwargs, True

            for relation_kwargs in relation_mapping['unexpired_objects_kwargs']:
                yield model_label, expired_object_kwargs, relation_mapping, relation_kwargs, False


@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize(
    'model_label,factory_kwargs,relation_mapping,relation_factory_kwargs,is_expired',
    _generate_run_args(),
)
@pytest.mark.django_db
def test_run(
    model_label,
    factory_kwargs,
    relation_mapping,
    relation_factory_kwargs,
    is_expired,
    track_return_values,
    setup_es,
):
    """Tests the delete_old_records commands for various cases specified by MAPPING above."""
    mapping = MAPPING[model_label]
    model_factory = mapping['factory']
    command = delete_old_records.Command()
    model = apps.get_model(model_label)

    delete_return_value_tracker = track_return_values(QuerySet, 'delete')

    obj = _create_model_obj(model_factory, **factory_kwargs)
    total_model_records = 1

    if relation_mapping:
        _create_model_obj(
            relation_mapping['factory'],
            **relation_factory_kwargs,
            **{relation_mapping['field']: obj},
        )
        if relation_mapping['factory']._meta.get_model_class() is model:
            total_model_records += 1

    num_expired_records = 1 if is_expired else 0

    search_app = get_search_app_by_model(model)
    doc_type = search_app.name
    read_alias = search_app.es_model.get_read_alias()

    setup_es.indices.refresh()
    assert model.objects.count() == total_model_records
    assert setup_es.count(read_alias, doc_type=doc_type)['count'] == total_model_records

    management.call_command(command, model_label)
    setup_es.indices.refresh()

    # Check if the object has been deleted
    assert model.objects.count() == total_model_records - num_expired_records
    assert setup_es.count(read_alias, doc_type=doc_type)['count'] == (
        total_model_records
        - num_expired_records
    )

    # Check which models were actually deleted
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]

    if is_expired:
        assert deletions_by_model[model._meta.label] == num_expired_records
        assert model._meta.label in {model._meta.label}

    actual_deleted_models = {  # only include models actually deleted
        deleted_model
        for deleted_model, deleted_count in deletions_by_model.items()
        if deleted_count
    }
    assert actual_deleted_models - {model._meta.label} <= mapping['implicitly_deletable_models']


@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize('model_name,config', delete_old_records.Command.CONFIGS.items())
@pytest.mark.usefixtures('disconnect_delete_search_signal_receivers')
@pytest.mark.django_db
def test_simulate(model_name, config, track_return_values, setup_es):
    """
    Test that if --simulate is passed in, the command only simulates the action
    without making any actual changes.
    """
    delete_return_value_tracker = track_return_values(QuerySet, 'delete')
    command = delete_old_records.Command()

    mapping = MAPPING[model_name]
    model_factory = mapping['factory']

    for _ in range(3):
        _create_model_obj(model_factory, **mapping['expired_object_kwargs'])

    setup_es.indices.refresh()

    model = apps.get_model(model_name)
    search_app = get_search_app_by_model(model)
    read_alias = search_app.es_model.get_read_alias()

    assert model.objects.count() == 3
    assert setup_es.count(read_alias, doc_type=search_app.name)['count'] == 3

    management.call_command(command, model_name, simulate=True)
    setup_es.indices.refresh()

    # Check which models were deleted prior to the rollback
    return_values = delete_return_value_tracker.return_values
    assert len(return_values) == 1
    _, deletions_by_model = return_values[0]
    actual_deleted_models = {  # only include models actually deleted
        deleted_model
        for deleted_model, deleted_count in deletions_by_model.items()
        if deleted_count
    }
    assert model._meta.label in {model._meta.label}
    assert actual_deleted_models - {model._meta.label} <= mapping['implicitly_deletable_models']
    assert deletions_by_model[model._meta.label] == 3

    # Check that nothing has actually been deleted
    assert model.objects.count() == 3
    assert setup_es.count(read_alias, doc_type=search_app.name)['count'] == 3


@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize('model_name,config', delete_old_records.Command.CONFIGS.items())
@pytest.mark.django_db
def test_only_print_queries(model_name, config, monkeypatch, caplog):
    """
    Test that if --only-print-queries is passed, the SQL query is printed but no deletions or
    simulation occurs.
    """
    caplog.set_level('INFO')
    delete_mock = mock.Mock()
    monkeypatch.setattr(QuerySet, 'delete', delete_mock)

    command = delete_old_records.Command()
    model = apps.get_model(model_name)
    mapping = MAPPING[model_name]
    model_factory = mapping['factory']

    for _ in range(3):
        _create_model_obj(model_factory, **mapping['expired_object_kwargs'])

    management.call_command(command, model_name, only_print_queries=True)

    assert not delete_mock.called

    log_text = caplog.text.lower()
    assert f'{model._meta.verbose_name_plural} to delete:' in log_text

    for relation in get_relations_to_delete(model):
        related_meta = relation.related_model._meta
        assert (
            f'{related_meta.verbose_name_plural} to delete '
            f'(via {related_meta.model_name}.{relation.remote_field.name}): '
        ) in log_text
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

    command = delete_old_records.Command()
    model_name = next(iter(delete_old_records.Command.CONFIGS))
    mapping = MAPPING[model_name]
    model_factory = MAPPING[model_name]['factory']

    _create_model_obj(model_factory, **mapping['expired_object_kwargs'])

    with pytest.raises(DataHubException):
        management.call_command(command, model_name)

    model = apps.get_model(model_name)
    assert model.objects.count() == 0


def _create_model_obj(factory, **field_value_mapping):
    with freeze_time(field_value_mapping.get('created_on', FROZEN_TIME)):
        obj = factory(**field_value_mapping)

    with freeze_time(field_value_mapping.get('modified_on', FROZEN_TIME)):
        obj.save()

    return obj


def _format_field(field):
    if field.name == '+':
        return f'{field.field.model.__name__}._meta.get_field({field.field.name!r}).remote_field'

    return f'{field.model.__name__}._meta.get_field({field.name!r})'
