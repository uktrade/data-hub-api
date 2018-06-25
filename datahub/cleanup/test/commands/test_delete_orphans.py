from datetime import timedelta

import pytest
from django.apps import apps
from django.core import management
from django.core.management.base import CommandError
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.cleanup.management.commands import delete_orphans
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.test.factories import to_many_field
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.leads.test.factories import BusinessLeadFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.omis.quote.test.factories import QuoteFactory


pytestmark = pytest.mark.django_db


class ShallowInvestmentProjectFactory(InvestmentProjectFactory):
    """
    Same as InvestmentProjectFactory but with reduced dependencies
    so that we can test specific references without extra noise.
    """

    intermediate_company = None
    investor_company = None
    uk_company = None

    @to_many_field
    def client_contacts(self):
        """No client contacts."""
        return []


"""
For each model in delete_orphans.ORPHANING_CONFIGS:
    - specify the factory class to create an instance
    - specify the list of dependent models as a tuple of:
        - dependent factory class to create an instance
        - dependent field name referencing the main model
"""
MAPPINGS = {
    'company.Contact': {
        'factory': ContactFactory,
        'dependent_models': (
            (CompanyInteractionFactory, 'contact'),
            (OrderFactory, 'contact'),
            (QuoteFactory, 'accepted_by'),
            (InvestmentProjectFactory, 'client_contacts'),
        )

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
        )
    },
    'event.Event': {
        'factory': EventFactory,
        'dependent_models': (
            (CompanyInteractionFactory, 'event'),
        )

    },
}


def pytest_generate_tests(metafunc):
    """
    Parametrizes the tests that use the `orphaning_mapping` fixture
    by getting each individual mapping dependency so that it can be
    tested separately.
    """
    if 'orphaning_mapping' in metafunc.fixturenames:
        view_data = []
        for model_name in delete_orphans.ORPHANING_CONFIGS:
            mapping = MAPPINGS[model_name]
            view_data += [
                (model_name, mapping['factory'], dep_factory, dep_field_name)
                for dep_factory, dep_field_name in mapping['dependent_models']
            ]

        metafunc.parametrize(
            'orphaning_mapping',
            view_data,
            ids=[
                f'{model_name}: {dep_factory._meta.model.__name__}.{dep_field_name}'
                for model_name, _, dep_factory, dep_field_name in view_data
            ]
        )


@pytest.mark.parametrize('model_name', delete_orphans.ORPHANING_CONFIGS)
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

    related_fields = delete_orphans.get_related_fields(model)
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


@freeze_time('2018-06-01 02:00')
def test_run(orphaning_mapping):
    """
    Test that:
        - a record without any objects referencing it but not old enough
            doesn't get deleted
        - a record without any objets referencing it and old gets deleted
        - a record with another object referencing it doesn't get deleted
    """
    model_name, model_factory, dep_factory, dep_field_name = orphaning_mapping
    orphaning_config = delete_orphans.ORPHANING_CONFIGS[model_name]

    non_orphaning_datetime = now() - timedelta(days=orphaning_config.days_before_orphaning)
    orphaning_datetime = non_orphaning_datetime - timedelta(days=1)

    # this orphan should NOT get deleted because not old enough
    create_orphanable_model(model_factory, orphaning_config, non_orphaning_datetime)

    # this orphan should get deleted because old
    create_orphanable_model(model_factory, orphaning_config, orphaning_datetime)

    # this object should NOT get deleted because it has another object referencing it
    non_orphan = create_orphanable_model(model_factory, orphaning_config, orphaning_datetime)
    is_m2m = dep_factory._meta.model._meta.get_field(dep_field_name).many_to_many
    dep_factory(
        **{dep_field_name: [non_orphan] if is_m2m else non_orphan},
    )

    # 3 + 1 in case of self-references
    total_model_records = 3 + (1 if dep_factory == model_factory else 0)

    model = apps.get_model(model_name)
    assert model.objects.count() == total_model_records
    management.call_command(delete_orphans.Command(), model_name)
    assert model.objects.count() == total_model_records - 1


@freeze_time('2018-06-01 02:00')
@pytest.mark.parametrize('model_name', delete_orphans.ORPHANING_CONFIGS)
def test_simulate(model_name, caplog):
    """
    Test that if --simulate=True is passed in, the command only simulates the action
    without making any actual changes.
    """
    caplog.set_level('INFO')

    orphaning_config = delete_orphans.ORPHANING_CONFIGS[model_name]
    mapping = MAPPINGS[model_name]
    model_factory = mapping['factory']
    orphaning_datetime = now() - timedelta(days=orphaning_config.days_before_orphaning + 1)

    for _ in range(3):
        create_orphanable_model(model_factory, orphaning_config, orphaning_datetime)

    model = apps.get_model(model_name)
    assert model.objects.count() == 3
    management.call_command(delete_orphans.Command(), model_name, simulate=True)
    assert model.objects.count() == 3

    # check that 3 records would have been deleted
    assert len(caplog.records) == 2
    assert 'to delete: 3' in caplog.records[0].message


def test_fails_with_invalid_model():
    """
    Test that if an invalid value for model is passed in, the command errors.
    """
    with pytest.raises(CommandError):
        management.call_command(delete_orphans.Command(), 'invalid')
