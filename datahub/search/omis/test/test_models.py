import pytest

from datahub.omis.order.test.factories import (
    OrderAssigneeFactory,
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderSubscriberFactory,
    OrderWithAcceptedQuoteFactory,
)
from datahub.search.omis import OrderSearchApp
from datahub.search.omis.models import Order as ESOrder

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'order_factory',
    (
        OrderCancelledFactory,
        OrderCompleteFactory,
        OrderFactory,
        OrderPaidFactory,
        OrderWithAcceptedQuoteFactory,
    ),
)
def test_order_to_dict(order_factory):
    """Test converting an order to dict."""
    order = order_factory()

    invoice = order.invoice
    OrderSubscriberFactory.create_batch(2, order=order)
    OrderAssigneeFactory.create_batch(2, order=order)

    result = ESOrder.db_object_to_dict(order)

    assert result == {
        '_document_type': OrderSearchApp.name,
        'id': order.pk,
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
        'created_on': order.created_on,
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
        'modified_on': order.modified_on,
        'reference': order.reference,
        'status': order.status,
        'description': order.description,
        'contacts_not_to_approach': order.contacts_not_to_approach,
        'further_info': order.further_info,
        'existing_agents': order.existing_agents,
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
                },
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
        'payment_due_date': None if not invoice else invoice.payment_due_date,
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
        'paid_on': order.paid_on,
        'completed_by': {
            'id': str(order.completed_by.pk),
            'first_name': order.completed_by.first_name,
            'last_name': order.completed_by.last_name,
            'name': order.completed_by.name,
        } if order.completed_by else None,
        'completed_on': order.completed_on,
        'cancelled_by': {
            'id': str(order.cancelled_by.pk),
            'first_name': order.cancelled_by.first_name,
            'last_name': order.cancelled_by.last_name,
            'name': order.cancelled_by.name,
        } if order.cancelled_by else None,
        'cancelled_on': order.cancelled_on,
        'cancellation_reason': {
            'id': str(order.cancellation_reason.pk),
            'name': order.cancellation_reason.name,
        } if order.cancellation_reason else None,
    }


def test_orders_to_es_documents():
    """Test converting 2 orders to Elasticsearch documents."""
    orders = OrderFactory.create_batch(2)

    result = ESOrder.db_objects_to_es_documents(orders)

    assert {item['_id'] for item in result} == {item.pk for item in orders}
