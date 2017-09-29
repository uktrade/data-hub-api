import pytest

from datahub.omis.order.test.factories import (
    OrderAssigneeFactory, OrderFactory, OrderSubscriberFactory
)

from ..models import Order as ESOrder

pytestmark = pytest.mark.django_db


def test_order_to_dict():
    """Test converting an order to dict."""
    order = OrderFactory()
    OrderSubscriberFactory.create_batch(2, order=order)
    OrderAssigneeFactory.create_batch(2, order=order)

    result = ESOrder.dbmodel_to_dict(order)

    assert result == {
        'id': str(order.pk),
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
        'created_on': order.created_on,
        'created_by': {
            'id': str(order.created_by.pk),
            'first_name': order.created_by.first_name,
            'last_name': order.created_by.last_name,
            'name': order.created_by.name
        },
        'modified_on': order.modified_on,
        'reference': order.reference,
        'status': order.status,
        'description': order.description,
        'contacts_not_to_approach': order.contacts_not_to_approach,
        'delivery_date': order.delivery_date,
        'contact_email': order.contact_email,
        'contact_phone': order.contact_phone,
        'subscribers': [
            {
                'id': str(subscriber.adviser.pk),
                'first_name': subscriber.adviser.first_name,
                'last_name': subscriber.adviser.last_name,
                'name': str(subscriber.adviser.name),
                'dit_team': {
                    'id': str(subscriber.adviser.dit_team.pk),
                    'name': str(subscriber.adviser.dit_team.name),
                }
            }
            for subscriber in order.subscribers.all()
        ],
        'assignees': [
            {
                'id': str(assignee.adviser.pk),
                'first_name': assignee.adviser.first_name,
                'last_name': assignee.adviser.last_name,
                'name': str(assignee.adviser.name),
                'dit_team': {
                    'id': str(assignee.adviser.dit_team.pk),
                    'name': str(assignee.adviser.dit_team.name),
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


def test_orders_to_es_documents():
    """Test converting 2 orders to Elasticsearch documents."""
    orders = OrderFactory.create_batch(2)

    result = ESOrder.dbmodels_to_es_documents(orders)

    assert {item['_id'] for item in result} == {str(item.pk) for item in orders}
