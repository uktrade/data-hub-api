from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company_activity.tests.factories import StovaEventFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
)
from datahub.metadata.test.factories import TeamFactory


class TestGetEventView(APITestMixin):
    """Get single event view tests."""

    def test_stova_event_details_no_permissions(self):
        """Should return 403"""
        stova_event = StovaEventFactory()
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company-activity:stova-event:detail', kwargs={'pk': stova_event.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get(self):
        """Test getting a single stova event."""
        stova_event = StovaEventFactory()
        url = reverse('api-v4:company-activity:stova-event:detail', kwargs={'pk': stova_event.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        expected_response_data = {
            'datahub_event': [str(stova_event.datahub_event.values_list('id', flat=True).last())],
            'id': str(stova_event.id),
            'stova_event_id': stova_event.stova_event_id,
            'name': stova_event.name,
            'description': stova_event.description,
            'code': stova_event.code,
            'created_by': stova_event.created_by,
            'modified_by': stova_event.modified_by,
            'client_contact': stova_event.client_contact,
            'contact_info': stova_event.contact_info,
            'country': stova_event.country,
            'city': stova_event.city,
            'state': stova_event.state,
            'timezone': stova_event.timezone,
            'url': stova_event.url,
            'max_reg': stova_event.max_reg,
            'created_date': format_date_or_datetime(stova_event.created_date),
            'modified_date': format_date_or_datetime(stova_event.modified_date),
            'start_date': format_date_or_datetime(stova_event.start_date),
            'live_date': format_date_or_datetime(stova_event.live_date),
            'close_date': stova_event.close_date,
            'end_date': format_date_or_datetime(stova_event.end_date),
            'location_state': stova_event.location_state,
            'location_country': stova_event.location_country,
            'location_address1': stova_event.location_address1,
            'location_address2': stova_event.location_address2,
            'location_address3': stova_event.location_address3,
            'location_city': stova_event.location_city,
            'location_name': stova_event.location_name,
            'location_postcode': stova_event.location_postcode,
            'approval_required': stova_event.approval_required,
            'price_type': stova_event.price_type,
            'folder_id': stova_event.folder_id,
            'default_language': stova_event.default_language,
            'standard_currency': stova_event.standard_currency,
        }

        assert response_data == expected_response_data
