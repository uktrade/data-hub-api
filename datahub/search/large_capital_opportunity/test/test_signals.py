from unittest import mock

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.queue import DataHubQueue
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.search.large_capital_opportunity.apps import LargeCapitalOpportunitySearchApp

pytestmark = pytest.mark.django_db


def _get_documents(setup_opensearch, pk):
    return setup_opensearch.get(
        index=LargeCapitalOpportunitySearchApp.search_model.get_read_alias(),
        id=pk,
    )


def test_new_large_capital_opportunity_synced(
    opensearch_with_signals,
    queue: DataHubQueue,
):
    """Test that new large capital opportunity is synced to OpenSearch."""
    opportunity = LargeCapitalOpportunityFactory()
    opensearch_with_signals.indices.refresh()
    assert _get_documents(opensearch_with_signals, opportunity.pk)


def test_updated_large_capital_opportunity_synced(
    opensearch_with_signals,
    queue: DataHubQueue,
):
    """Test that when a large capital opportunity is updated it is synced to OpenSearch."""
    opportunity = LargeCapitalOpportunityFactory()
    opportunity.total_investment_sought = 12345
    opportunity.save()
    opensearch_with_signals.indices.refresh()
    doc = _get_documents(opensearch_with_signals, opportunity.pk)
    assert doc['_source']['total_investment_sought'] == 12345


def test_delete_from_opensearch(opensearch_with_signals, queue: DataHubQueue):
    """
    Test that when a large capital opportunity is deleted from db it also
    calls delete document to delete from OpenSearch.
    """
    opportunity = LargeCapitalOpportunityFactory()
    opensearch_with_signals.indices.refresh()

    assert _get_documents(opensearch_with_signals, opportunity.pk)

    with mock.patch(
        'datahub.search.large_capital_opportunity.signals.delete_document',
    ) as mock_delete_document:
        opportunity.delete()
        opensearch_with_signals.indices.refresh()
        assert mock_delete_document.called is True


def test_edit_promoter_syncs_large_capital_opportunity_in_opensearch(
    opensearch_with_signals,
    queue: DataHubQueue,
):
    """
    Tests that updating promoter company details also updated the relevant
    large capital opportunity.
    """
    new_company_name = 'SYNC TEST'
    promoter = CompanyFactory()
    opportunity = LargeCapitalOpportunityFactory(promoters=[promoter])
    opensearch_with_signals.indices.refresh()
    promoter.name = new_company_name
    promoter.save()

    result = _get_documents(opensearch_with_signals, opportunity.pk)
    assert result['_source']['promoters'][0]['name'] == new_company_name
