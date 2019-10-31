from datetime import datetime

import pytest
from django.utils.timezone import utc
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_adviser(adviser):
    """Returns adviser data as a dictionary"""
    return {
        'id': str(adviser.id),
        'date_joined': format_date_or_datetime(adviser.date_joined),
        'first_name': adviser.first_name,
        'last_name': adviser.last_name,
        'telephone_number': adviser.telephone_number,
        'contact_email': adviser.contact_email,
        'dit_team_id': str(adviser.dit_team.id),
        'is_active': adviser.is_active,
    }


@pytest.mark.django_db
class TestAdviserDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for the advisers data-flow export endpoint
    """

    view_url = reverse('api-v4:dataset:advisers-dataset')
    factory = AdviserFactory

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single company"""
        adviser = AdviserFactory()
        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_200_OK

        assert response.json()['results'] == [get_expected_data_from_adviser(adviser)]

    def test_with_multiple_advisers(self, data_flow_api_client):
        """Test that endpoint returns correct order of records"""
        adviser_1 = AdviserFactory(date_joined=datetime(2019, 1, 2, tzinfo=utc))
        adviser_2 = AdviserFactory(date_joined=datetime(2019, 1, 3, tzinfo=utc))
        adviser_3 = AdviserFactory(date_joined=datetime(2019, 1, 1, tzinfo=utc))
        adviser_4 = AdviserFactory(date_joined=datetime(2019, 1, 1, tzinfo=utc))

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        assert [a['id'] for a in response.json()['results']] == [
            str(a.id)
            for a in sorted([adviser_3, adviser_4], key=lambda x: x.id) + [adviser_1, adviser_2]
        ]
