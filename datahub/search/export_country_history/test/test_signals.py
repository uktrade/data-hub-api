import pytest
from opensearchpy.exceptions import NotFoundError

from datahub.company.models import CompanyExportCountryHistory
from datahub.company.test.factories import CompanyExportCountryHistoryFactory
from datahub.search.export_country_history.apps import ExportCountryHistoryApp

pytestmark = pytest.mark.django_db


def test_new_export_country_history_synced(opensearch_with_signals):
    """Test that new export country history is synced to OpenSearch."""
    company_export_country_history = CompanyExportCountryHistoryFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=ExportCountryHistoryApp.search_model.get_write_index(),
        id=company_export_country_history.pk,
    )


def test_updated_interaction_synced(opensearch_with_signals):
    """Test that when export country history is updated, it is synced to OpenSearch."""
    export_country_history = CompanyExportCountryHistoryFactory(
        history_type=CompanyExportCountryHistory.HistoryType.INSERT,
    )
    history_type = CompanyExportCountryHistory.HistoryType.UPDATE
    export_country_history.history_type = history_type
    export_country_history.save()
    opensearch_with_signals.indices.refresh()

    result = opensearch_with_signals.get(
        index=ExportCountryHistoryApp.search_model.get_write_index(),
        id=export_country_history.pk,
    )

    assert result['_source'] == {
        '_document_type': ExportCountryHistoryApp.name,
        'history_user': {
            'id': str(export_country_history.history_user.id),
            'name': export_country_history.history_user.name,
        },
        'country': {
            'id': str(export_country_history.country.id),
            'name': export_country_history.country.name,
        },
        'company': {
            'id': str(export_country_history.company.id),
            'name': export_country_history.company.name,
        },
        'id': str(export_country_history.pk),
        'history_type': export_country_history.history_type,
        'history_date': export_country_history.history_date.isoformat(),
        'date': export_country_history.history_date.isoformat(),
        'status': str(export_country_history.status),
    }


def test_deleting_export_country_history_removes_from_opensearch(opensearch_with_signals):
    company_export_country_history = CompanyExportCountryHistoryFactory()

    opensearch_with_signals.indices.refresh()

    doc = opensearch_with_signals.get(
        index=ExportCountryHistoryApp.search_model.get_read_alias(),
        id=company_export_country_history.pk,
    )
    assert doc['_source']['company']['name'] == company_export_country_history.company.name
    assert doc['_source']['company']['id'] == str(company_export_country_history.company_id)

    company_export_country_history_id = company_export_country_history.id
    company_export_country_history.delete()

    opensearch_with_signals.indices.refresh()

    with pytest.raises(NotFoundError):
        doc = opensearch_with_signals.get(
            index=ExportCountryHistoryApp.search_model.get_read_alias(),
            id=company_export_country_history_id,
        )
