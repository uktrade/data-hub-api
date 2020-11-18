import pytest

from datahub.omis.order.test.factories import (
    OrderAssigneeFactory,
    OrderFactory,
    OrderSubscriberFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.search.omis import OrderSearchApp

pytestmark = pytest.mark.django_db


def test_creating_order_syncs_to_es(es_with_signals):
    """Test that when I create an order, it gets synced to ES."""
    order = OrderFactory()
    es_with_signals.indices.refresh()

    assert es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )


def test_updating_order_updates_es(es_with_signals):
    """Test that when I update an order, the updated version gets synced to ES."""
    order = OrderFactory()
    new_description = 'lorem'
    order.description = new_description
    order.save()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )
    assert result['_source']['description'] == new_description


def test_accepting_quote_updates_es(es_with_signals):
    """
    Test that when a quote is accepted and the invoice created, the payment_due_date field
    in ES gets updated.
    """
    order = OrderWithOpenQuoteFactory()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )
    assert not result['_source']['payment_due_date']

    order.accept_quote(by=None)
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )
    assert result['_source']['payment_due_date'] == order.invoice.payment_due_date.isoformat()


def test_adding_subscribers_syncs_order_to_es(es_with_signals):
    """
    Test that when a subscriber is added to an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory()
    subscribers = OrderSubscriberFactory.create_batch(2, order=order)
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )

    indexed = {str(subscriber['id']) for subscriber in result['_source']['subscribers']}
    expected = {str(subscriber.adviser.pk) for subscriber in subscribers}
    assert indexed == expected
    assert len(indexed) == 2


def test_removing_subscribers_syncs_order_to_es(es_with_signals):
    """
    Test that when a subscriber is removed from an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory()
    subscribers = OrderSubscriberFactory.create_batch(2, order=order)
    subscribers.pop().delete()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )

    indexed = {str(subscriber['id']) for subscriber in result['_source']['subscribers']}
    expected = {str(subscriber.adviser.pk) for subscriber in subscribers}
    assert indexed == expected
    assert len(indexed) == 1


def test_adding_assignees_syncs_order_to_es(es_with_signals):
    """
    Test that when an assignee is added to an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory(assignees=[])
    assignees = OrderAssigneeFactory.create_batch(2, order=order)
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )

    indexed = {str(assignee['id']) for assignee in result['_source']['assignees']}
    expected = {str(assignee.adviser.pk) for assignee in assignees}
    assert indexed == expected
    assert len(indexed) == 2


def test_removing_assignees_syncs_order_to_es(es_with_signals):
    """
    Test that when an assignee is removed from an order,
    the linked order gets synced to ES.
    """
    order = OrderFactory(assignees=[])
    assignees = OrderAssigneeFactory.create_batch(2, order=order)
    assignees.pop().delete()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )

    indexed = {str(assignee['id']) for assignee in result['_source']['assignees']}
    expected = {str(assignee.adviser.pk) for assignee in assignees}
    assert indexed == expected
    assert len(indexed) == 1


def test_updating_company_name_updates_orders(es_with_signals):
    """Test that when a company name is updated, the company's orders are synced to ES."""
    order = OrderFactory()
    new_company_name = 'exogenous'
    order.company.name = new_company_name
    order.company.save()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )
    assert result['_source']['company']['name'] == new_company_name


def test_updating_contact_name_updates_orders(es_with_signals):
    """Test that when a contact's name is updated, the contacts's orders are synced to ES."""
    order = OrderFactory()
    new_first_name = 'Jamie'
    new_last_name = 'Bloggs'

    contact = order.contact
    contact.first_name = new_first_name
    contact.last_name = new_last_name
    contact.save()
    es_with_signals.indices.refresh()

    result = es_with_signals.get(
        index=OrderSearchApp.es_model.get_write_index(),
        id=order.pk,
    )
    assert result['_source']['contact'] == {
        'id': str(contact.pk),
        'first_name': new_first_name,
        'last_name': new_last_name,
        'name': f'{new_first_name} {new_last_name}',
    }
