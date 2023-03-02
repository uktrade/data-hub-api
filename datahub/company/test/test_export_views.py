import uuid

import pytest

from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    AdviserFactory,
    ExportFactory,
)
from datahub.core.test_utils import APITestMixin, format_date_or_datetime

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestPatchExport(APITestMixin):
    """Test the PATCH export endpoint"""

    def test_patch_unknown_export_returns_error(self):
        """Test a PATCH with an unknown export id returns a not found error"""
        ExportFactory.create_batch(3)
        url = reverse('api-v4:export:item', kwargs={'pk': uuid.uuid4()})

        response = self.api_client.patch(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_too_many_team_members_return_expected_error(self):
        """
        Test when the number of team_members provided is above the maximum allowed, the response
        contains this error message
        """
        export = ExportFactory()
        url = reverse('api-v4:export:item', kwargs={'pk': export.id})

        response = self.api_client.patch(
            url, data={'team_members': [advisor.id for advisor in AdviserFactory.create_batch(6)]}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_success(self):
        """
        Test a PATCH request with a known export id provides a success response
        """
        modified_date = now()
        with freeze_time(modified_date):
            export = ExportFactory()
            url = reverse('api-v4:export:item', kwargs={'pk': export.id})

            response = self.api_client.patch(url, data={'title': 'New title'})

            assert response.status_code == status.HTTP_200_OK

            assert response.json() == {
                'id': str(export.pk),
                'archived': False,
                'archived_by': None,
                'archived_on': None,
                'archived_reason': None,
                'company': {'id': str(export.company.id), 'name': export.company.name},
                'contacts': [
                    {'id': str(contact.id), 'name': contact.name}
                    for contact in export.contacts.all()
                ],
                'created_by': None,
                'created_on': format_date_or_datetime(export.created_on),
                'destination_country': {
                    'id': str(export.destination_country.id),
                    'name': export.destination_country.name,
                },
                'estimated_export_value_amount': str(export.estimated_export_value_amount),
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
                'modified_by': str(self.user.id),
                'modified_on': format_date_or_datetime(modified_date),
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
                'title': 'New title',
            }
