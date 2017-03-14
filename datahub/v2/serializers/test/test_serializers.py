import datetime

import colander
import pytest

from datahub.v2.serializers.service_deliveries import ServiceDeliverySchema


def test_service_deliveries_serializer():
    data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'subject': 'whatever',
                'date': datetime.datetime.now().isoformat(),
                'notes': 'hello',
                'feedback': 'foo'
            },
            'relationships': {
                'status': {
                    'data': {
                        'type': 'ServiceDeliveryStatus',
                        'id': 'constants.ServiceDeliveryStatus.offered.value.id'
                    }
                },
                'company': {
                    'data': {
                        'type': 'Company',
                        'id': 'CompanyFactory().pk'
                    }
                },
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': 'ContactFactory().pk'
                    }
                },
                'service': {
                    'data': {
                        'type': 'Service',
                        'id': 'service_offer.service.id'
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': 'service_offer.dit_team.id'
                    }
                },
                'uk_region': {
                    'data': {
                        'type': 'UKRegion',
                        'id': 'dsdasdsadsa'
                    }
                },
                'sector': {
                    'data': {
                        'type': 'Sector',
                        'id': 'dsdasdsadsa'
                    }
                },
                'country_of_interest': {
                    'data': {
                        'type': 'flibble',
                        'id': 'dsdasdsadsa'
                    }
                },
                'event': {
                    'data': {
                        'type': 'event',
                        'id': 'dsdasdsadsa'
                    }
                },
            }
        }

    with pytest.raises(colander.Invalid) as e:
        result = ServiceDeliverySchema().deserialize(data)
    import ipdb; ipdb.set_trace()
    assert e.asdict()
