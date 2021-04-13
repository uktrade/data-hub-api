from unittest import mock

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.search.large_capital_opportunity.apps import LargeCapitalOpportunitySearchApp

pytestmark = pytest.mark.django_db


def _get_es_document(setup_es, pk):
    return setup_es.get(
        index=LargeCapitalOpportunitySearchApp.es_model.get_read_alias(),
        id=pk,
    )


def test_new_large_capital_opportunity_synced(es_with_signals):
    """Test that new large capital opportunity is synced to ES."""
    opportunity = LargeCapitalOpportunityFactory()
    es_with_signals.indices.refresh()
    assert _get_es_document(es_with_signals, opportunity.pk)


def test_updated_large_capital_opportunity_synced(es_with_signals):
    """Test that when a large capital opportunity is updated it is synced to ES."""
    opportunity = LargeCapitalOpportunityFactory()
    opportunity.total_investment_sought = 12345
    opportunity.save()
    es_with_signals.indices.refresh()
    doc = _get_es_document(es_with_signals, opportunity.pk)
    assert doc['_source']['total_investment_sought'] == 12345


def test_delete_from_es(es_with_signals):
    """
    Test that when a large capital opportunity is deleted from db it also
    calls delete document to delete from ES.
    """
    opportunity = LargeCapitalOpportunityFactory()
    es_with_signals.indices.refresh()

    assert _get_es_document(es_with_signals, opportunity.pk)

    with mock.patch(
        'datahub.search.large_capital_opportunity.signals.delete_document',
    ) as mock_delete_document:
        opportunity.delete()
        es_with_signals.indices.refresh()
        assert mock_delete_document.called is True


def test_edit_promoter_syncs_large_capital_opportunity_in_es(es_with_signals):
    """
    Tests that updating promoter company details also updated the relevant
    large capital opportunity.
    """
    new_company_name = 'SYNC TEST'
    promoter = CompanyFactory()
    opportunity = LargeCapitalOpportunityFactory(promoters=[promoter])
    es_with_signals.indices.refresh()
    promoter.name = new_company_name
    promoter.save()

    result = _get_es_document(es_with_signals, opportunity.pk)
    assert result['_source']['promoters'][0]['name'] == new_company_name
