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
                'assignees': {
                    'properties': {
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'type': 'keyword'
                                },
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text'
                                }
                            },
                            'type': 'nested'
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'id': {
                            'type': 'keyword'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'billing_address_1': {
                    'type': 'text'
                },
                'billing_address_2': {
                    'type': 'text'
                },
                'billing_address_country': {
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'billing_address_county': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'billing_address_postcode': {
                    'type': 'text'
                },
                'billing_address_town': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'billing_contact_name': {
                    'type': 'text'
                },
                'billing_email': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'billing_phone': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'company': {
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'contact': {
                    'properties': {
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'id': {
                            'type': 'keyword'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'contact_email': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'contact_phone': {
                    'type': 'keyword'
                },
                'contacts_not_to_approach': {
                    'type': 'text'
                },
                'created_by': {
                    'properties': {
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'id': {
                            'type': 'keyword'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'created_on': {
                    'type': 'date'
                },
                'delivery_date': {
                    'type': 'date'
                },
                'description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text'
                },
                'discount_value': {
                    'index': False,
                    'type': 'integer'
                },
                'id': {
                    'type': 'keyword'
                },
                'modified_on': {
                    'type': 'date'
                },
                'net_cost': {
                    'index': False,
                    'type': 'integer'
                },
                'po_number': {
                    'index': False,
                    'type': 'keyword'
                },
                'primary_market': {
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'reference': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'sector': {
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'service_types': {
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'status': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'subscribers': {
                    'properties': {
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'type': 'keyword'
                                },
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text'
                                }
                            },
                            'type': 'nested'
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'id': {
                            'type': 'keyword'
                        },
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'subtotal_cost': {
                    'index': False,
                    'type': 'integer'
                },
                'total_cost': {
                    'type': 'integer'
                },
                'vat_cost': {
                    'index': False,
                    'type': 'integer'
                },
                'vat_number': {
                    'index': False,
                    'type': 'keyword'
                },
                'vat_status': {
                    'index': False,
                    'type': 'keyword'
                },
                'vat_verified': {
                    'index': False,
                    'type': 'boolean'
                }
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
            'status': order.status,
            'description': order.description,
            'contacts_not_to_approach': order.contacts_not_to_approach,
            'delivery_date': order.delivery_date.isoformat(),
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'subscribers': [
                {
                    'id': str(subscriber.adviser.pk),
                    'name': subscriber.adviser.name,
                    'first_name': subscriber.adviser.first_name,
                    'last_name': subscriber.adviser.last_name,
                }
                for subscriber in order.subscribers.all()
            ],
            'assignees': [
                {
                    'id': str(assignee.adviser.pk),
                    'name': assignee.adviser.name,
                    'first_name': assignee.adviser.first_name,
                    'last_name': assignee.adviser.last_name,
                    'dit_team': {
                        'id': str(assignee.adviser.dit_team.id),
                        'name': assignee.adviser.dit_team.name,
                    }
                }
                for assignee in order.assignees.all()
            ],
            'po_number': order.po_number,
            'discount_value': order.discount_value,
            'vat_status': order.vat_status,
            'vat_number': order.vat_number,
            'vat_verified': order.vat_verified,
            'net_cost': order.net_cost,
            'subtotal_cost': order.subtotal_cost,
            'vat_cost': order.vat_cost,
            'total_cost': order.total_cost,
            'billing_contact_name': order.billing_contact_name,
            'billing_email': order.billing_email,
            'billing_phone': order.billing_phone,
            'billing_address_1': order.billing_address_1,
            'billing_address_2': order.billing_address_2,
            'billing_address_town': order.billing_address_town,
            'billing_address_county': order.billing_address_county,
            'billing_address_postcode': order.billing_address_postcode,
            'billing_address_country': {
                'id': str(order.billing_address_country.pk),
                'name': order.billing_address_country.name
            },
        }
    }
