import pytest

from datahub.company.models import CompanyExportCountryHistory as DBCompanyExportCountryHistory
from datahub.company.test.factories import CompanyExportCountryHistoryFactory
from datahub.search.export_country_history.apps import ExportCountryHistoryApp

pytestmark = pytest.mark.django_db


def test_new_export_country_history_synced(es_with_signals):
    """Test that new export country history is synced to ES."""
    company_export_country_history = CompanyExportCountryHistoryFactory()
    es_with_signals.indices.refresh()

    assert es_with_signals.get(
        index=ExportCountryHistoryApp.es_model.get_write_index(),
        doc_type=ExportCountryHistoryApp.name,
        id=company_export_country_history.pk,
    )


def test_updated_interaction_synced(es_with_signals):
    """Test that when export country history is updated, it is synced to ES."""
    export_country_history = CompanyExportCountryHistoryFactory(
        history_type=DBCompanyExportCountryHistory.HistoryType.INSERT,
    )
    history_type = DBCompanyExportCountryHistory.HistoryType.UPDATE
    export_country_history.history_type = history_type
    export_country_history.save()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=ExportCountryHistoryApp.es_model.get_write_index(),
        doc_type=ExportCountryHistoryApp.name,
        id=export_country_history.pk,
    )

    assert result['_source'] == {
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
