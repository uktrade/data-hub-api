import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import format_date_or_datetime, get_attr_or_none
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.user.company_list.test.factories import (
    ArchivedPipelineItemFactory,
    PipelineItemFactory,
)


def get_expected_data_from_pipeline_item(item):
    """Returns pipeline item data as a dictionary"""
    return {
        'adviser_id': str(item.adviser_id),
        'archived': item.archived,
        'company_id': str(item.company_id),
        'contact_ids': [str(contact.id) for contact in item.contacts.all()] or None,
        'created_on': format_date_or_datetime(item.created_on),
        'expected_win_date': (
            format_date_or_datetime(item.expected_win_date)
            if item.expected_win_date else None
        ),
        'id': str(item.id),
        'likelihood_to_win': item.likelihood_to_win,
        'modified_on': format_date_or_datetime(item.modified_on),
        'name': item.name,
        'potential_value': item.potential_value,
        'sector_name': get_attr_or_none(item, 'sector.name'),
        'status': item.status,
    }


@pytest.mark.django_db
class TestPipelineItemDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for PipelineItemsDatasetView
    """

    view_url = reverse('api-v4:dataset:pipeline-items-dataset')
    factory = PipelineItemFactory

    @pytest.mark.parametrize(
        'item_factory', (
            PipelineItemFactory,
            ArchivedPipelineItemFactory,
        ),
    )
    def test_success(self, data_flow_api_client, item_factory):
        """Test that endpoint returns with expected data for a single pipeline item"""
        item = item_factory()
        item.contacts.add(ContactFactory())
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_pipeline_item(item)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        with freeze_time('2019-01-01 12:30:00'):
            item1 = PipelineItemFactory()
        with freeze_time('2019-01-03 12:00:00'):
            item2 = PipelineItemFactory()
        with freeze_time('2019-01-01 12:00:00'):
            item3 = PipelineItemFactory()
            item4 = ArchivedPipelineItemFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted([item3, item4], key=lambda x: x.pk) + [item1, item2]
        for index, item in enumerate(expected_list):
            assert str(item.id) == response_results[index]['id']
