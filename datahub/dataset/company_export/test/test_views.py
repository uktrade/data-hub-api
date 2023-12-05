from datetime import datetime

import pytest
from django.urls import reverse
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import ContactFactory
from datahub.company.test.factories import ExportFactory
from datahub.core.test_utils import format_date_or_datetime, get_attr_or_none
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_company_export(export):
    """Returns company export data as a dictionary"""
    return {
        'owner_id': str(export.owner_id),
        'archived': export.archived,
        'archived_by_id': export.archived_by_id,
        'archived_on': (
            format_date_or_datetime(export.archived_on)
            if export.archived_on else None
        ),
        'archived_reason': export.archived_reason,
        'company_id': str(export.company_id),
        'contact_ids': [str(contact.id) for contact in export.contacts.all()] or None,
        'created_on': format_date_or_datetime(export.created_on),
        'created_by_id': export.created_by_id,
        'modified_on': format_date_or_datetime(export.modified_on),
        'modified_by_id': export.modified_by_id,
        'estimated_win_date': (
            format_date_or_datetime(export.estimated_win_date)
            if export.estimated_win_date else None
        ),
        'id': str(export.id),
        'title': export.title,
        'estimated_export_value_amount': export.estimated_export_value_amount,
        'sector_name': get_attr_or_none(export, 'sector.name'),
        'status': export.status.name.lower(),
        'destination_country__name': export.destination_country.name,
        'destination_country__iso_alpha2_code': export.destination_country.iso_alpha2_code,
        'estimated_export_value_years__name': export.estimated_export_value_years.name,
        'exporter_experience__name': export.exporter_experience.name,
        'notes': export.notes,
        'export_potential': export.export_potential,
        'team_member_ids': [str(adviser.id) for adviser in export.team_members.all()] or None,
    }


@pytest.mark.django_db
class TestCompanyExportDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for CompanyExportDatasetView
    """

    view_url = reverse('api-v4:dataset:company-export-dataset')
    factory = ExportFactory

    @pytest.mark.parametrize(
        'item_factory', (
            ExportFactory,
            ExportFactory,
        ),
    )
    def test_success(self, data_flow_api_client, item_factory):
        """Test that endpoint returns with expected data for a single pipeline item"""
        export = item_factory()
        export.contacts.add(ContactFactory())
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_company_export(export)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        with freeze_time('2019-01-01 12:30:00'):
            export1 = ExportFactory()
        with freeze_time('2019-01-03 12:00:00'):
            export2 = ExportFactory()
        with freeze_time('2019-01-01 12:00:00'):
            export3 = ExportFactory()
            export4 = ExportFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted([export3, export4], key=lambda x: x.pk) + [export1, export2]
        for index, item in enumerate(expected_list):
            assert str(item.id) == response_results[index]['id']

    def test_with_updated_since_filter(self, data_flow_api_client):
        with freeze_time('2021-01-01 12:30:00'):
            ExportFactory()
        with freeze_time('2022-01-01 12:30:00'):
            company_export_after = ExportFactory()
        # Define the `updated_since` date
        updated_since_date = datetime(2021, 2, 1, tzinfo=utc).strftime('%Y-%m-%d')

        # Make the request with the `updated_since` parameter
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})

        assert response.status_code == status.HTTP_200_OK

        # Check that only companies created after the `updated_since` date are returned
        expected_ids = [str(company_export_after.id)]
        response_ids = [company['id'] for company in response.json()['results']]

        assert response_ids == expected_ids
