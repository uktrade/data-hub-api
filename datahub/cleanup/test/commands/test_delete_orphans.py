from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django.apps import apps
from django.core import management
from django.utils.timezone import utc

from datahub.cleanup.management.commands import delete_orphans
from datahub.cleanup.query_utils import get_related_fields
from datahub.cleanup.test.commands.factories import ShallowInvestmentProjectFactory
from datahub.cleanup.test.commands.test_common import create_orphanable_model
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.exceptions import DataHubException
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.leads.test.factories import BusinessLeadFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.omis.quote.test.factories import QuoteFactory

pytestmark = pytest.mark.django_db

CONFIGS = delete_orphans.Command.CONFIGS


"""
For each model in the CONFIG attribute for clean-up management commands:
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
    'interaction.Interaction': {
        'factory': CompanyInteractionFactory,
        'dependent_models': (),
    }
}


@pytest.mark.parametrize('model_name', CONFIGS)
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


@mock.patch('datahub.search.deletion.bulk')
@pytest.mark.usefixtures('synchronous_on_commit')
def test_with_es_exception(mocked_bulk):
    """
    Test that if ES returns a 5xx error, the command completes but it also
    raises a DataHubException with details of the error.
    """
    mocked_bulk.return_value = (None, [{'delete': {'status': 500}}])

    model_name = next(iter(delete_orphans.Command.CONFIGS))
    model_factory = MAPPINGS[model_name]['factory']
    orphaning_config = delete_orphans.Command.CONFIGS[model_name]

    orphaning_datetime = today(tzinfo=utc) - orphaning_config.age_threshold - relativedelta(days=1)
    create_orphanable_model(model_factory, orphaning_config, orphaning_datetime)

    with pytest.raises(DataHubException):
        management.call_command(delete_orphans.Command(), model_name)

    model = apps.get_model(model_name)
    assert model.objects.count() == 0
