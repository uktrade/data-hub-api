import pytest
from elasticsearch_dsl import Mapping

from datahub.omis.order.test.factories import (
    OrderCancelledFactory, OrderCompleteFactory,
    OrderFactory, OrderPaidFactory,
    OrderWithAcceptedQuoteFactory
)
from .. import OrderSearchApp
from ..models import Order as ESOrder
from ... import elasticsearch

pytestmark = pytest.mark.django_db


def test_mapping(setup_es):
    """Test the ES mapping for an order."""
    mapping = Mapping.from_es(OrderSearchApp.es_model.get_write_index(), OrderSearchApp.name)

    assert mapping.to_dict() == {
        'order': {
            'dynamic': 'false',
            'properties': {
                'assignees': {
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
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
                            'copy_to': ['assignees.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
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
                    'include_in_parent': True,
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
                'billing_company_name': {
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
                'cancellation_reason': {
                    'include_in_parent': True,
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
                'cancelled_by': {
                    'include_in_parent': True,
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
                            'copy_to': ['cancelled_by.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'cancelled_on': {
                    'type': 'date'
                },
                'company': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'copy_to': ['company.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text'
                        },
                        'trading_name': {
                            'copy_to': ['company.trading_name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'trading_name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'completed_by': {
                    'include_in_parent': True,
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
                            'copy_to': ['completed_by.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'completed_on': {
                    'type': 'date'
                },
                'contact': {
                    'include_in_parent': True,
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
                            'copy_to': ['contact.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
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
                    'include_in_parent': True,
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
                            'copy_to': ['created_by.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text'
                        },
                        'dit_team': {
                            'include_in_parent': True,
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
                'existing_agents': {
                    'index': False,
                    'type': 'text'
                },
                'further_info': {
                    'type': 'text'
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
                'paid_on': {
                    'type': 'date'
                },
                'payment_due_date': {
                    'type': 'date'
                },
                'po_number': {
                    'index': False,
                    'type': 'keyword'
                },
                'primary_market': {
                    'include_in_parent': True,
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
                    'copy_to': ['reference_trigram'],
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'reference_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text'
                },
                'sector': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'ancestors': {
                            'include_in_parent': True,
                            'properties': {
                                'id': {
                                    'type': 'keyword'
                                }
                            },
                            'type': 'nested'
                        }
                    },
                    'type': 'nested'
                },
                'uk_region': {
                    'include_in_parent': True,
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
                    'include_in_parent': True,
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
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
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
                            'copy_to': ['subscribers.name_trigram'],
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'subtotal_cost': {
                    'copy_to': ['subtotal_cost_string'],
                    'type': 'integer'
                },
                'subtotal_cost_string': {
                    'type': 'keyword'
                },
                'total_cost': {
                    'copy_to': ['total_cost_string'],
                    'type': 'integer'
                },
                'total_cost_string': {
                    'type': 'keyword'
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


@pytest.mark.parametrize(
    'Factory',  # noqa: N803
    (
        OrderFactory,
        OrderWithAcceptedQuoteFactory,
        OrderCancelledFactory,
        OrderCompleteFactory,
        OrderPaidFactory,
    )
)
def test_indexed_doc(Factory, setup_es):
    """Test the ES data of an indexed order."""
    order = Factory()
    invoice = order.invoice

    doc = ESOrder.es_document(order)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    setup_es.indices.refresh()

    indexed_order = setup_es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk
    )

    assert indexed_order == {
        '_index': OrderSearchApp.es_model.get_target_index_name(),
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
                'name': order.created_by.name,
                'dit_team': {
                    'id': str(order.created_by.dit_team.id),
                    'name': order.created_by.dit_team.name
                }
            },
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name,
                'trading_name': order.company.alias,
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
                'name': order.sector.name,
                'ancestors': [{
                    'id': str(ancestor.pk),
                } for ancestor in order.sector.get_ancestors()]
            },
            'uk_region': {
                'id': str(order.uk_region.pk),
                'name': order.uk_region.name
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
            'further_info': order.further_info,
            'existing_agents': order.existing_agents,
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
            'payment_due_date': None if not invoice else invoice.payment_due_date.isoformat(),
            'subtotal_cost': order.subtotal_cost,
            'vat_cost': order.vat_cost,
            'total_cost': order.total_cost,
            'billing_company_name': order.billing_company_name,
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
            'paid_on': order.paid_on.isoformat() if order.paid_on else None,
            'completed_by': {
                'id': str(order.completed_by.pk),
                'first_name': order.completed_by.first_name,
                'last_name': order.completed_by.last_name,
                'name': order.completed_by.name
            } if order.completed_by else None,
            'completed_on': order.completed_on.isoformat() if order.completed_on else None,
            'cancelled_by': {
                'id': str(order.cancelled_by.pk),
                'first_name': order.cancelled_by.first_name,
                'last_name': order.cancelled_by.last_name,
                'name': order.cancelled_by.name
            } if order.cancelled_by else None,
            'cancelled_on': order.cancelled_on.isoformat() if order.cancelled_on else None,
            'cancellation_reason': {
                'id': str(order.cancellation_reason.pk),
                'name': order.cancellation_reason.name
            } if order.cancellation_reason else None,
        }
    }
