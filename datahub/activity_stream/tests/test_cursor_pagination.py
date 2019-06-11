import pytest
from django.conf import settings
from rest_framework import status

from datahub.activity_stream.tests import hawk
from datahub.activity_stream.tests.utils import get_url
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
def test_cursor_pagination(api_client, factory, endpoint):
    """
    Test if pagination behaves as expected
    """
    page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    interactions = factory.create_batch(page_size + 1)
    response = hawk.get(api_client, get_url(endpoint))
    assert response.status_code == status.HTTP_200_OK

    page_1_data = response.json()
    page_2_url = page_1_data['next']
    assert len(page_1_data['orderedItems']) == page_size

    response = hawk.get(api_client, page_2_url)
    page_2_data = response.json()
    page_1_url = page_2_data['previous']
    assert len(page_2_data['orderedItems']) == len(interactions) - page_size

    response = hawk.get(api_client, page_1_url)
    page_1_data_2 = response.json()
    assert page_1_data['orderedItems'] == page_1_data_2['orderedItems']
    assert page_1_data_2['next'] == page_2_url
