import datetime

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
    """
    Test if pagination behaves as expected
    """
    page_size = 2
    monkeypatch.setattr(
        'datahub.activity_stream.pagination.ActivityCursorPagination.page_size',
        page_size,
    )

    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start):
        interactions = factory.create_batch(page_size + 1)
        response = hawk.get(api_client, get_url(endpoint))
        assert response.status_code == status.HTTP_200_OK

        page_1_data = response.json()
        page_2_url = page_1_data['next']
        assert len(page_1_data['orderedItems']) == page_size

        response = hawk.get(api_client, page_2_url)
        page_2_data = response.json()
        assert len(page_2_data['orderedItems']) == len(interactions) - page_size
