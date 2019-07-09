import pytest
from rest_framework import status

from datahub.activity_stream.tests import hawk
from datahub.activity_stream.tests.utils import get_url
from datahub.core.test_utils import format_date_or_datetime
from datahub.omis.order.test.factories import OrderFactory


@pytest.mark.parametrize(
    'order_overrides',
    (
        {},
        {'created_by_id': None},
        {'primary_market_id': None},
        {'uk_region_id': None},
    ),
)
@pytest.mark.django_db
def test_omis_order_added_activity(api_client, order_overrides):
    """
    Get a list of OMIS Orders added and test the JSON returned is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    order = OrderFactory(**order_overrides)
    response = hawk.get(api_client, get_url('api-v3:activity-stream:omis-order-added'))
    assert response.status_code == status.HTTP_200_OK

    expected_data = {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'OMIS Order Added Activity',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/omis/order-added',
        'partOf': 'http://testserver/v3/activity-stream/omis/order-added',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubOMISOrder:{order.id}:Add',
                'type': 'Add',
                'published': format_date_or_datetime(order.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubOMISOrder:{order.id}',
                    'type': ['dit:OMISOrder'],
                    'startTime': format_date_or_datetime(order.created_on),
                    'name': order.reference,
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{order.company.pk}',
                            'dit:dunsNumber': order.company.duns_number,
                            'dit:companiesHouseNumber': order.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': order.company.name,
                        },
                        {
                            'id': f'dit:DataHubContact:{order.contact.pk}',
                            'type': ['Person', 'dit:Contact'],
                            'url': order.contact.get_absolute_url(),
                            'dit:emailAddress': order.contact.email,
                            'dit:jobTitle': order.contact.job_title,
                            'name': order.contact.name,
                        },
                    ],
                    'url': order.get_absolute_url(),
                },
            },
        ],
    }

    if 'created_by_id' not in order_overrides:
        expected_data['orderedItems'][0]['actor'] = {
            'id': f'dit:DataHubAdviser:{order.created_by.pk}',
            'type': ['Person', 'dit:Adviser'],
            'dit:emailAddress':
                order.created_by.contact_email or order.created_by.email,
            'name': order.created_by.name,
        }

    if 'primary_market_id' not in order_overrides:
        expected_data['orderedItems'][0]['object']['dit:country'] = {
            'name': order.primary_market.name,
        }

    if 'uk_region_id' not in order_overrides:
        expected_data['orderedItems'][0]['object']['dit:ukRegion'] = {
            'name': order.uk_region.name,
        }

    assert response.json() == expected_data
