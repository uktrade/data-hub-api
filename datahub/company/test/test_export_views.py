import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    AdviserFactory,
    ContactFactory,
    ExportFactory,
)
from datahub.core.test_utils import APITestMixin, format_date_or_datetime

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestGetExport(APITestMixin):
    """Test get export"""

    def test_get_success(self):

        export = ExportFactory(
            contacts=ContactFactory.create_batch(3),
            team_members=AdviserFactory.create_batch(4),
        )

        url = reverse('api-v4:export:item', kwargs={'pk': export.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.json() == {
            'id': str(export.pk),
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company': {'id': str(export.company.id), 'name': export.company.name},
            'contacts': [
                {'id': str(contact.id), 'name': contact.name} for contact in export.contacts.all()
            ],
            'created_by': None,
            'created_on': format_date_or_datetime(export.created_on),
            'destination_country': {
                'id': str(export.destination_country.id),
                'name': export.destination_country.name,
            },
            'estimated_export_value_amount': export.estimated_export_value_amount,
            'estimated_export_value_years': {
                'id': str(export.estimated_export_value_years.id),
                'name': export.estimated_export_value_years.name,
            },
            'estimated_win_date': format_date_or_datetime(export.estimated_win_date),
            'export_potential': export.export_potential,
            'exporter_experience': {
                'id': str(export.exporter_experience.id),
                'name': export.exporter_experience.name,
            },
            'modified_by': None,
            'modified_on': format_date_or_datetime(export.modified_on),
            'notes': export.notes,
            'owner': {
                'id': str(export.owner.id),
                'name': export.owner.name,
            },
            'sector': {
                'id': str(export.sector.id),
                'name': export.sector.name,
            },
            'status': export.status,
            'team_members': [
                {'id': str(team_member.id), 'name': team_member.name}
                for team_member in export.team_members.all()
            ],
            'title': export.title,
        }
