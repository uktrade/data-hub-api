# -*- coding: utf-8 -*-

import datetime
import unittest

import colander
import pytest

from datahub.v2.serializers.service_deliveries import ServiceDeliverySchema, RelationshipType


class TestRelationshipType(unittest.TestCase):
    def setUp(self):
        class MySchema(colander.MappingSchema):
            item = colander.SchemaNode(RelationshipType("flibble"))
        self.schema = MySchema

    def test_deserialize_empty(self):
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {}})
        assert e.value.asdict()['item'] == '{} has no key data'

    def test_deserialize_missing_type(self):
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {'data': {}}})
        assert e.value.asdict()['item'] == """{'data': {}} has no key type"""

    def test_deserialize_incorrect_type(self):
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {'data': {'type': "bamble"}}})
        print(e.value.asdict()['item'])
        assert e.value.asdict()['item'] == "type bamble should be flibble"

    def test_serialize_empty(self):
        with pytest.raises(colander.Invalid) as e:
            self.schema().serialize({'item': {}})
        assert e.value.asdict()['item'] == '{} has no key data'

    def test_serialize_missing_type(self):
        with pytest.raises(colander.Invalid) as e:
            self.schema().serialize({'item': {'data': {}}})
        assert e.value.asdict()['item'] == """{'data': {}} has no key type"""

    def test_serialize_incorrect_type(self):
        with pytest.raises(colander.Invalid) as e:
            self.schema().serialize({'item': {'data': {'type': "bamble"}}})
        assert e.value.asdict()['item'] == "type bamble should be flibble"


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

    expected = {
        'relationships.country_of_interest': 'type flibble should be Country',
        'relationships.event': 'type event should be Event',
        'relationships.status': 'type ServiceDeliveryStatus should be Status'}

    with pytest.raises(colander.Invalid) as e:
        ServiceDeliverySchema().deserialize(data)

    assert e.value.asdict() == expected
