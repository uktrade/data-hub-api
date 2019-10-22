import pytest
from elasticsearch_dsl import Mapping

from datahub.omis.order.test.factories import (
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
)
from datahub.search import elasticsearch
from datahub.search.omis import OrderSearchApp
from datahub.search.omis.models import Order as ESOrder

pytestmark = pytest.mark.django_db


def test_mapping(es):
    """Test the ES mapping for an order."""
    mapping = Mapping.from_es(OrderSearchApp.es_model.get_write_index(), OrderSearchApp.name)

    assert mapping.to_dict() == {
        'order': {
            'dynamic': 'false',
            'properties': {
                'assignees': {
                    'properties': {
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'type': 'keyword',
                                },
                                'name': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                            },
                            'type': 'object',
                        },
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                    },
                    'type': 'object',
                },
                'billing_address_1': {
                    'type': 'text',
                },
                'billing_address_2': {
                    'type': 'text',
                },
                'billing_address_country': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'billing_address_county': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'billing_address_postcode': {
                    'type': 'text',
                },
                'billing_address_town': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'billing_contact_name': {
                    'type': 'text',
                },
                'billing_company_name': {
                    'type': 'text',
                },
                'billing_email': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'billing_phone': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'cancellation_reason': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'cancelled_by': {
                    'properties': {
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                    },
                    'type': 'object',
                },
                'cancelled_on': {
                    'type': 'date',
                },
                'company': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                        'trading_names': {
                            'type': 'text',
                            'fields': {
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                    },
                    'type': 'object',
                },
                'completed_by': {
                    'properties': {
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                    },
                    'type': 'object',
                },
                'completed_on': {
                    'type': 'date',
                },
                'contact': {
                    'properties': {
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                    },
                    'type': 'object',
                },
                'contact_email': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'contact_phone': {
                    'type': 'keyword',
                },
                'contacts_not_to_approach': {
                    'type': 'text',
                },
                'created_by': {
                    'properties': {
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'type': 'keyword',
                                },
                                'name': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                            },
                            'type': 'object',
                        },
                    },
                    'type': 'object',
                },
                'created_on': {
                    'type': 'date',
                },
                'delivery_date': {
                    'type': 'date',
                },
                'description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'discount_value': {
                    'index': False,
                    'type': 'integer',
                },
                'existing_agents': {
                    'index': False,
                    'type': 'text',
                },
                'further_info': {
                    'type': 'text',
                },
                'id': {
                    'type': 'keyword',
                },
                'modified_on': {
                    'type': 'date',
                },
                'net_cost': {
                    'index': False,
                    'type': 'integer',
                },
                'paid_on': {
                    'type': 'date',
                },
                'payment_due_date': {
                    'type': 'date',
                },
                'po_number': {
                    'index': False,
                    'type': 'keyword',
                },
                'primary_market': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'reference': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                    'fields': {
                        'trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                },
                'sector': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'ancestors': {
                            'properties': {
                                'id': {
                                    'type': 'keyword',
                                },
                            },
                            'type': 'object',
                        },
                    },
                    'type': 'object',
                },
                'uk_region': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'service_types': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'status': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'subscribers': {
                    'properties': {
                        'dit_team': {
                            'properties': {
                                'id': {
                                    'type': 'keyword',
                                },
                                'name': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                            },
                            'type': 'object',
                        },
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                        },
                    },
                    'type': 'object',
                },
                'subtotal_cost': {
                    'type': 'integer',
                    'fields': {
                        'keyword': {
                            'type': 'keyword',
                        },
                    },
                },
                'total_cost': {
                    'type': 'integer',
                    'fields': {
                        'keyword': {
                            'type': 'keyword',
                        },
                    },
                },
                'vat_cost': {
                    'index': False,
                    'type': 'integer',
                },
                'vat_number': {
                    'index': False,
                    'type': 'keyword',
                },
                'vat_status': {
                    'index': False,
                    'type': 'keyword',
                },
                'vat_verified': {
                    'index': False,
                    'type': 'boolean',
                },
            },
        },
    }


@pytest.mark.parametrize(
    'order_factory',
    (
        OrderFactory,
        OrderWithAcceptedQuoteFactory,
        OrderCancelledFactory,
        OrderCompleteFactory,
        OrderPaidFactory,
    ),
)
def test_indexed_doc(order_factory, es):
    """Test the ES data of an indexed order."""
    order = order_factory()
    invoice = order.invoice

    doc = ESOrder.es_document(order)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    es.indices.refresh()

    indexed_order = es.get(
        index=OrderSearchApp.es_model.get_write_index(),
        doc_type=OrderSearchApp.name,
        id=order.pk,
    )

    assert indexed_order['_id'] == str(order.pk)
    assert indexed_order['_source'] == {
        'id': str(order.pk),
        'created_by': {
            'id': str(order.created_by.pk),
            'first_name': order.created_by.first_name,
            'last_name': order.created_by.last_name,
            'name': order.created_by.name,
            'dit_team': {
                'id': str(order.created_by.dit_team.id),
                'name': order.created_by.dit_team.name,
            },
        },
        'company': {
            'id': str(order.company.pk),
            'name': order.company.name,
            'trading_names': order.company.trading_names,
        },
        'contact': {
            'id': str(order.contact.pk),
            'first_name': order.contact.first_name,
            'last_name': order.contact.last_name,
            'name': order.contact.name,
        },
        'primary_market': {
            'id': str(order.primary_market.pk),
            'name': order.primary_market.name,
        },
        'sector': {
            'id': str(order.sector.pk),
            'name': order.sector.name,
            'ancestors': [{
                'id': str(ancestor.pk),
            } for ancestor in order.sector.get_ancestors()],
        },
        'uk_region': {
            'id': str(order.uk_region.pk),
            'name': order.uk_region.name,
        },
        'service_types': [
            {
                'id': str(service_type.pk),
                'name': service_type.name,
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
                },
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
            'name': order.billing_address_country.name,
        },
        'paid_on': order.paid_on.isoformat() if order.paid_on else None,
        'completed_by': {
            'id': str(order.completed_by.pk),
            'first_name': order.completed_by.first_name,
            'last_name': order.completed_by.last_name,
            'name': order.completed_by.name,
        } if order.completed_by else None,
        'completed_on': order.completed_on.isoformat() if order.completed_on else None,
        'cancelled_by': {
            'id': str(order.cancelled_by.pk),
            'first_name': order.cancelled_by.first_name,
            'last_name': order.cancelled_by.last_name,
            'name': order.cancelled_by.name,
        } if order.cancelled_by else None,
        'cancelled_on': order.cancelled_on.isoformat() if order.cancelled_on else None,
        'cancellation_reason': {
            'id': str(order.cancellation_reason.pk),
            'name': order.cancellation_reason.name,
        } if order.cancellation_reason else None,
    }
