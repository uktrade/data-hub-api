from unittest import mock

import pytest

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.test_utils import synchronous_executor_submit, synchronous_transaction_on_commit
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.search import elasticsearch

from ..company.models import Company
from ..contact.models import Contact
from ..investment.models import InvestmentProject

pytestmark = pytest.mark.django_db


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
@mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
def test_company_auto_sync_to_es(setup_data, post_save_handlers):
    """Tests if company gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_company'
    CompanyFactory(
        name=test_name
    )
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(test_name, entities=(Company,)).execute()

    assert result.hits.total == 1


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
@mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
def test_company_auto_updates_to_es(setup_data, post_save_handlers):
    """Tests if company gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_company_international'
    company = CompanyFactory(
        name=test_name
    )
    new_test_name = 'very_hard_to_find_company_local'
    company.name = new_test_name
    company.save()
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(new_test_name, entities=(Company,)).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == str(company.id)


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
@mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
def test_contact_auto_sync_to_es(setup_data, post_save_handlers):
    """Tests if contact gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_contact'
    ContactFactory(
        first_name=test_name
    )
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(test_name, entities=(Contact,)).execute()

    assert result.hits.total == 1


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
@mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
def test_contact_auto_updates_to_es(setup_data, post_save_handlers):
    """Tests if contact gets updated in Elasticsearch."""
    test_name = 'very_hard_to_find_contact_ii'
    contact = ContactFactory(
        first_name=test_name
    )
    contact.save()

    new_test_name = 'very_hard_to_find_contact_v'
    contact.first_name = new_test_name
    contact.save()
    setup_data.indices.refresh()

    result = elasticsearch.get_basic_search_query(new_test_name, entities=(Contact,)).execute()

    assert result.hits.total == 1
    assert result.hits[0].id == str(contact.id)


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
@mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
def test_investment_project_auto_sync_to_es(setup_data, post_save_handlers):
    """Tests if investment project gets synced to Elasticsearch."""
    test_name = 'very_hard_to_find_project'
    InvestmentProjectFactory(
        name=test_name
    )
    setup_data.indices.refresh()

    result = elasticsearch.get_search_by_entity_query(
        term='',
        filters={'name': test_name},
        entity=InvestmentProject
    ).execute()

    assert result.hits.total == 1


@mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
@mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
def test_investment_project_auto_updates_to_es(setup_data, post_save_handlers):
    """Tests if investment project gets synced to Elasticsearch."""
    project = InvestmentProjectFactory()
    new_test_name = 'even_harder_to_find_investment_project'
    project.name = new_test_name
    project.save()
    setup_data.indices.refresh()

    result = elasticsearch.get_search_by_entity_query(
        term='',
        filters={'name': new_test_name},
        entity=InvestmentProject
    ).execute()

    assert result.hits.total == 1
