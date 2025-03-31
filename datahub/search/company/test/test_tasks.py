import datetime
import logging
from operator import attrgetter

import pytest

from datahub.company.test.factories import AdviserFactory, CompanyFactory, SubsidiaryFactory
from datahub.core.test.queues.test_scheduler import PickleableMock
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.search.company.tasks import (
    schedule_sync_investment_projects_of_subsidiary_companies,
    sync_investment_projects_of_subsidiary_companies,
)
from datahub.search.investment.models import InvestmentProject
from datahub.search.query_builder import get_search_by_entities_query

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_sync_investment_projects_of_subsidiary_companies(monkeypatch):
    """Mocks the sync_investment_projects_of_subsidiary_companies function."""
    mock_sync_investment_projects_of_subsidiary_companies = PickleableMock()
    monkeypatch.setattr(
        'datahub.search.company.tasks.sync_investment_projects_of_subsidiary_companies',
        mock_sync_investment_projects_of_subsidiary_companies.queue_handler,
    )
    return mock_sync_investment_projects_of_subsidiary_companies


def test_schedule_sync_investment_projects_of_subsidiary_companies(
    caplog,
    mock_sync_investment_projects_of_subsidiary_companies,
):
    """Test that the sync_investment_projects_of_subsidiary_companies function is called from the
    scheduler.
    """
    caplog.set_level(logging.INFO, logger='datahub.search.company.tasks')
    subsidiary = SubsidiaryFactory()

    job = schedule_sync_investment_projects_of_subsidiary_companies(
        subsidiary.global_headquarters,
        subsidiary.modified_on,
    )

    assert caplog.messages == [
        f'Task {job.id} schedule_sync_investment_projects_of_subsidiary_companies '
        f'scheduled company {subsidiary.global_headquarters}',
    ]
    assert mock_sync_investment_projects_of_subsidiary_companies.called is True
    assert mock_sync_investment_projects_of_subsidiary_companies.keywords[0] == {
        'company': subsidiary.global_headquarters,
        'original_modified_on': subsidiary.modified_on,
    }


def test_sync_investment_projects_of_subsidiary_companies(
    opensearch_with_collector,
    mock_sync_investment_projects_of_subsidiary_companies,
):
    """Test that the sync_investment_projects_of_subsidiary_companies function is called from the
    scheduler for related subsidiaries/investment projects.
    """
    unrelated_owner = AdviserFactory()
    unrelated_company = CompanyFactory()
    unrelated_company.one_list_account_owner = unrelated_owner
    InvestmentProjectFactory.create_batch(
        3,
        investor_company=unrelated_company,
    )
    account_owner = AdviserFactory()
    subsidiary = SubsidiaryFactory()
    investment_projects = InvestmentProjectFactory.create_batch(3, investor_company=subsidiary)
    subsidiary.global_headquarters.one_list_account_owner = account_owner
    subsidiary.global_headquarters.save()
    opensearch_with_collector.flush_and_refresh()

    sync_investment_projects_of_subsidiary_companies(
        subsidiary.global_headquarters,
        subsidiary.modified_on,
    )

    assert mock_sync_investment_projects_of_subsidiary_companies.called is True
    result = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'one_list_group_global_account_manager.id': account_owner.id},
    ).execute()
    assert result.hits.total.value == 3
    # Map UUID to str for correct comparison
    investment_project_ids = map(attrgetter('id'), investment_projects)
    investment_project_ids = map(str, investment_project_ids)
    assert set(map(attrgetter('id'), result.hits)) == set(investment_project_ids)


def test_race_condition_sync_investment_projects_of_subsidiary_companies(
    opensearch_with_collector,
    mock_sync_investment_projects_of_subsidiary_companies,
):
    """Test that the race condition exception is raised when appropirate."""
    account_owner = AdviserFactory()
    subsidiary = SubsidiaryFactory()
    subsidiary.global_headquarters.one_list_account_owner = account_owner
    subsidiary.global_headquarters.save()
    opensearch_with_collector.flush_and_refresh()
    original_modified_on = subsidiary.modified_on + datetime.timedelta(hours=1)

    with pytest.raises(Exception) as exception_info:  # noqa: PT011
        sync_investment_projects_of_subsidiary_companies(
            subsidiary.global_headquarters,
            original_modified_on,
        )

    assert mock_sync_investment_projects_of_subsidiary_companies.called is True
    hq = subsidiary.global_headquarters
    assert exception_info.value.extra_info == (
        f'Company id: {hq.id}, '
        f'Company modified_on: {hq.modified_on}, '
        f'original_modified_on: {original_modified_on}.'
    )
    # Due to error investment projects shouldn't have been updated
    result = get_search_by_entities_query(
        [InvestmentProject],
        term='',
        filter_data={'one_list_group_global_account_manager.id': account_owner.id},
    ).execute()
    assert result.hits.total.value == 0
