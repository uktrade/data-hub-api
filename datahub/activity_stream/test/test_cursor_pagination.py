import base64
import datetime
import urllib.parse

import pytest
from freezegun import freeze_time
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.test.factories import OrderFactory


@pytest.mark.parametrize(
    'factory, endpoint',
    (
        (CompanyInteractionFactory, 'api-v3:activity-stream:interactions'),
        (InvestmentProjectFactory, 'api-v3:activity-stream:investment-project-added'),
        (OrderFactory, 'api-v3:activity-stream:omis-order-added'),
    ),
)
@pytest.mark.django_db
def test_cursor_pagination(factory, endpoint, api_client, monkeypatch):
    """Test if pagination behaves as expected
    """
    page_size = 2
    monkeypatch.setattr(
        'datahub.activity_stream.pagination.ActivityCursorPagination.page_size',
        page_size,
    )

    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        interactions = factory.create_batch(page_size + 1)
        frozen_datetime.tick(datetime.timedelta(seconds=1))

        response = hawk.get(api_client, get_url(endpoint))
        assert response.status_code == status.HTTP_200_OK
        page_0_data = response.json()
        assert len(page_0_data['orderedItems']) == 0

        frozen_datetime.tick(datetime.timedelta(microseconds=1))

        response = hawk.get(api_client, get_url(endpoint))
        assert response.status_code == status.HTTP_200_OK

        page_1_data = response.json()
        page_2_url = page_1_data['next']
        assert len(page_1_data['orderedItems']) == page_size

        response = hawk.get(api_client, page_2_url)
        page_2_data = response.json()
        page_3_url = page_2_data['next']
        assert len(page_2_data['orderedItems']) == len(interactions) - page_size

        response = hawk.get(api_client, page_3_url)
        page_3_data = response.json()
        assert len(page_3_data['orderedItems']) == 0
        assert page_3_data['next'] is None

        interactions = factory.create_batch(1)
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))

        response = hawk.get(api_client, page_3_url)
        page_3_post_update_data = response.json()
        assert len(page_3_post_update_data['orderedItems']) == 1

        page_4_url = page_3_post_update_data['next']
        response = hawk.get(api_client, page_4_url)
        page_4_data = response.json()
        assert len(page_4_data['orderedItems']) == 0
        assert page_4_data['next'] is None

        # Assert that DRF's cursor works, to not break existing pagination just after deployment
        now = datetime.datetime.now().isoformat(timespec='microseconds')
        cursor = base64.b64encode((f'p={urllib.parse.quote(now)}').encode()).decode()

        frozen_datetime.tick(datetime.timedelta(microseconds=1))
        interactions = factory.create_batch(1)

        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, f'{get_url(endpoint)}?cursor={cursor}')
        page_drf_data = response.json()
        assert len(page_drf_data['orderedItems']) == 1
