import pytest
from django.conf import settings
from elasticsearch_dsl import Mapping

from datahub.omis.order.test.factories import OrderFactory

from .. import OrderSearchApp
from ..models import Order as ESOrder
from ... import elasticsearch

pytestmark = pytest.mark.django_db


def test_mapping(setup_es):
    """Test the ES mapping for an order."""
    mapping = Mapping.from_es(settings.ES_INDEX, OrderSearchApp.name)

    assert mapping.to_dict() == {
        'order': {
            'properties': {
                'id': {
                    'index': 'not_analyzed',
                    'type': 'string'
                },
                'reference': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'type': 'string'
                },
                'company': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        }
                    },
                    'type': 'nested'
                },
                'contact': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        }
                    },
                    'type': 'nested'
                },
                'created_by': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        }
                    },
                    'type': 'nested'
                },
                'created_on': {
                    'format': 'strict_date_optional_time||epoch_millis',
                    'type': 'date'
                },
                'modified_on': {
                    'format': 'strict_date_optional_time||epoch_millis',
                    'type': 'date'
                },
                'primary_market': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        }
                    },
                    'type': 'nested'
                },
                'sector': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        }
                    },
                    'type': 'nested'
                },
                'description': {
                    'analyzer': 'english_analyzer',
                    'type': 'string'
                },
                'contacts_not_to_approach': {
                    'type': 'string'
                },
                'delivery_date': {
                    'format': 'strict_date_optional_time||epoch_millis',
                    'type': 'date'
                },
                'service_types': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        }
                    },
                    'type': 'nested'
                },
                'contact_email': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'type': 'string'
                },
                'contact_phone': {
                    'index': 'not_analyzed',
                    'type': 'string'
                },
                'subscribers': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'index': 'not_analyzed',
                                    'type': 'string'
                                },
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'type': 'string'
                                }
                            },
                            'type': 'nested'
                        }
                    },
                    'type': 'nested'
                },
                'assignees': {
                    'properties': {
                        'id': {
                            'index': 'not_analyzed',
                            'type': 'string'
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'type': 'string'
                        },
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'index': 'not_analyzed',
                                    'type': 'string'
                                },
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'type': 'string'
                                }
                            },
                            'type': 'nested'
                        }
                    },
                    'type': 'nested'
                },
            }
        }
    }


def test_indexed_doc(setup_es):
    """Test the ES data of an indexed order."""
    order = OrderFactory()

    doc = ESOrder.es_document(order)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    setup_es.indices.refresh()

    indexed_order = setup_es.get(
        index=settings.ES_INDEX,
        doc_type=OrderSearchApp.name,
        id=order.pk
    )

    assert indexed_order == {
        '_index': settings.ES_INDEX,
        '_type': OrderSearchApp.name,
        '_id': str(order.pk),
        '_version': indexed_order['_version'],
        'found': True,
        '_source': {
            'id': str(order.pk),
            'created_by': {
                'id': str(order.created_by.pk),
                'first_name': order.created_by.first_name,
                'last_name': order.created_by.last_name,
                'name': order.created_by.name
            },
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name
            },
            'contact': {
                'id': str(order.contact.pk),
                'first_name': order.contact.first_name,
                'last_name': order.contact.last_name,
                'name': order.contact.name
            },
            'primary_market': {
                'id': str(order.primary_market.pk),
                'name': order.primary_market.name
            },
            'sector': {
                'id': str(order.sector.pk),
                'name': order.sector.name
            },
            'service_types': [
                {
                    'id': str(service_type.pk),
                    'name': service_type.name
                }
                for service_type in order.service_types.all()
            ],
            'created_on': order.created_on.isoformat(),
            'modified_on': order.modified_on.isoformat(),
            'reference': order.reference,
            'description': order.description,
            'contacts_not_to_approach': order.contacts_not_to_approach,
            'delivery_date': order.delivery_date.isoformat(),
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'subscribers': [
                {
                    'id': str(subscriber.adviser.pk),
                    'name': str(subscriber.adviser.name),
                }
                for subscriber in order.subscribers.all()
            ],
            'assignees': [
                {
                    'id': str(subscriber.adviser.pk),
                    'name': str(subscriber.adviser.name),
                }
                for subscriber in order.assignees.all()
            ],
        }
    }
