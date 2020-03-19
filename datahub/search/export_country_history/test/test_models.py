import pytest

from datahub.company.test.factories import CompanyExportCountryHistoryFactory
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.export_country_history.models import ExportCountryHistory

pytestmark = pytest.mark.django_db


def test_export_country_history_to_dict(es):
    """Test for export country history search model"""
    export_country_history = CompanyExportCountryHistoryFactory()
    result = ExportCountryHistory.db_object_to_dict(export_country_history)

    assert result == {
        '_document_type': ExportCountryHistoryApp.name,
        'id': export_country_history.pk,
        'company': {
            'id': str(export_country_history.company.pk),
            'name': export_country_history.company.name,
        },
        'country': {
            'id': str(export_country_history.country.pk),
            'name': export_country_history.country.name,
        },
        'history_date': export_country_history.history_date,
        'date': export_country_history.history_date,
        'history_type': export_country_history.history_type,
        'history_user': {
            'id': str(export_country_history.history_user.pk),
            'name': export_country_history.history_user.name,
        },
        'status': export_country_history.status,
    }
