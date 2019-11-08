import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.event.test.factories import DisabledEventFactory, EventFactory


def get_expected_data_from_event(event):
    """Returns event data as a dictionary"""
    return {
        'address_1': event.address_1,
        'address_2': event.address_2,
        'address_country__name': event.address_country.name,
        'address_county': event.address_county,
        'address_postcode': event.address_postcode,
        'address_town': event.address_town,
        'created_on': format_date_or_datetime(event.created_on),
        'end_date': format_date_or_datetime(event.end_date),
        'event_type__name': event.event_type.name,
        'id': str(event.id),
        'lead_team_id': str(event.lead_team_id),
        'location_type__name': event.location_type.name,
        'name': event.name,
        'notes': event.notes,
        'organiser_id': str(event.organiser_id),
        'service_name': event.service.name,
        'start_date': format_date_or_datetime(event.start_date),
        'team_ids': [str(x.id) for x in event.teams.all().order_by('id')],
        'uk_region__name': event.uk_region.name,
    }


@pytest.mark.django_db
class TestEventDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for the events dataset endpoint
    """

    view_url = reverse('api-v4:dataset:events-dataset')
    factory = EventFactory

    @pytest.mark.parametrize(
        'event_factory', (
            EventFactory,
            DisabledEventFactory,
        ))
    def test_success(self, data_flow_api_client, event_factory):
        """Test that endpoint returns with expected data for a single event"""
        event = event_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_event(event)
        assert result == expected_result

    def test_with_multiple_events(self, data_flow_api_client):
        """Test that endpoint returns correct order of event records"""
        with freeze_time('2019-01-01 12:30:00'):
            event_1 = EventFactory()
        with freeze_time('2019-01-03 12:00:00'):
            event_2 = EventFactory()
        with freeze_time('2019-01-01 12:00:00'):
            event_3 = EventFactory()
            event_4 = EventFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_event_list = sorted([event_3, event_4], key=lambda x: x.pk) + [event_1, event_2]
        for index, event in enumerate(expected_event_list):
            assert str(event.id) == response_results[index]['id']
