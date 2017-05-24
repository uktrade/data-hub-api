"""Service deliveries schema tests."""

import datetime
import unittest
import uuid

import colander
import pytest

from datahub.core.test_utils import get_test_user
from datahub.v2.schemas.service_deliveries import ServiceDeliverySchema
from datahub.v2.schemas.utils import RelationshipType


class TestRelationshipType(unittest.TestCase):
    """Relationship type."""

    def setUp(self):
        """Create a dummy schema."""
        class MySchema(colander.MappingSchema):
            item = colander.SchemaNode(RelationshipType('flibble'))
        self.schema = MySchema

    def test_deserialize_empty(self):
        """Deserialize empty."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {}})
        assert e.value.asdict()['item'] == '{} has no key data'  # noqa: P103

    def test_deserialize_missing_type(self):
        """Deserialize missing type."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {'data': {'id': 1}}})
        assert e.value.asdict()['item'] == """{'data': {'id': 1}} has no key type"""

    def test_deserialize_missing_id(self):
        """Deserialize missing id."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {'data': {'type': 'foo'}}})
        assert e.value.asdict()['item'] == """{'data': {'type': 'foo'}} has no key id"""

    def test_deserialize_incorrect_type(self):
        """Deserialize incorrect type."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().deserialize({'item': {'data': {'id': 1, 'type': 'bamble'}}})
        assert e.value.asdict()['item'] == 'type bamble should be flibble'

    def test_serialize_empty(self):
        """Serialize empty."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().serialize({'item': {}})
        assert e.value.asdict()['item'] == '{} has no key data'  # noqa: P103

    def test_serialize_missing_type(self):
        """Serialize missing type."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().serialize({'item': {'data': {}}})
        assert e.value.asdict()['item'] == """{'data': {}} has no key type"""

    def test_serialize_incorrect_type(self):
        """Serialize incorrect type."""
        with pytest.raises(colander.Invalid) as e:
            self.schema().serialize({'item': {'data': {'type': 'bamble'}}})
        assert e.value.asdict()['item'] == 'type bamble should be flibble'


def test_service_deliveries_schema_invalid():
    """SD schema test."""
    data = {
        'type': 'ServiceDeliver',
        'id': 'hello',
        'attributes': {
            'subject': 'whatever',
            'date': datetime.datetime.now().isoformat(),
            'notes': 'hello',
            'feedback': 'foo',
        },
        'relationships': {
            'status': {
                'data': {
                    'type': 'Status',
                    'id': str(uuid.uuid4()),
                }
            },
            'company': {
                'data': {
                    'type': 'Company',
                    'id': str(uuid.uuid4()),
                }
            },
            'contact': {
                'data': {
                    'type': 'Contact',
                    'id': str(uuid.uuid4()),
                }
            },
            'service': {
                'data': {
                    'type': 'Service',
                    'id': str(uuid.uuid4()),
                }
            },
            'dit_team': {
                'data': {
                    'type': 'Team',
                    'id': str(uuid.uuid4()),
                }
            },
            'uk_region': {
                'data': {
                    'type': 'UKRegion',
                    'id': str(uuid.uuid4()),
                }
            },
            'sector': {
                'data': {
                    'type': 'Sector',
                    'id': str(uuid.uuid4()),
                }
            },
            'country_of_interest': {
                'data': {
                    'type': 'flibble',
                    'id': str(uuid.uuid4()),
                }
            },
            'event': {
                'data': {
                    'type': 'event',
                    'id': str(uuid.uuid4()),
                }
            },
        }
    }

    expected = {
        'id': 'Invalid UUID string',
        'type': 'Value must be ServiceDelivery',
        'relationships.dit_adviser': 'Required',
        'relationships.country_of_interest': 'type flibble should be Country',
        'relationships.event': 'type event should be Event',
        'relationships.status': 'type Status should be ServiceDeliveryStatus'}

    with pytest.raises(colander.Invalid) as e:
        ServiceDeliverySchema().deserialize(data)
    assert e.value.asdict() == expected


@pytest.mark.django_db
def test_service_deliveries_valid_schema():
    """SD schema test."""
    user = get_test_user()
    data = {
        'type': 'ServiceDelivery',
        'id': str(uuid.uuid4()),
        'attributes': {
            'subject': 'whatever',
            'date': datetime.datetime.now().isoformat(),
            'notes': 'hello',
        },
        'relationships': {
            'status': {
                'data': {
                    'type': 'ServiceDeliveryStatus',
                    'id': str(uuid.uuid4()),
                }
            },
            'company': {
                'data': {
                    'type': 'Company',
                    'id': str(uuid.uuid4()),
                }
            },
            'contact': {
                'data': {
                    'type': 'Contact',
                    'id': str(uuid.uuid4()),
                }
            },
            'service': {
                'data': {
                    'type': 'Service',
                    'id': str(uuid.uuid4()),
                }
            },
            'dit_team': {
                'data': {
                    'type': 'Team',
                    'id': str(uuid.uuid4()),
                }
            },
            'dit_adviser': {
                'data': {
                    'type': 'Advisor',
                    'id': str(user.pk)
                }
            }
        }
    }

    assert ServiceDeliverySchema().deserialize(data)
