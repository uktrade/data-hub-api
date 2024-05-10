from datetime import date

from django.core.management import BaseCommand

from datahub.company.models import Advisor, Contact
from datahub.omis.order.models import Order
from datahub.omis.order.serializers import OrderAssigneeSerializer
from datahub.omis.payment.models import Payment


class Command(BaseCommand):
    """
    Command to complete the order creation process after initial test data added to database
    by adding an assignee to the order, generating a quote, then marking it as paid.
    Example of executing the command locally:
        python manage.py set_order_as_paid
    """

    help = 'Complete order creation process once test data has been added to the database'

    def handle(self, *args, **options):
        """Adds assignee with the hours and making them the lead, and generates the quote"""
        order = Order.objects.get(pk='4ec5ceec-c23e-4243-9fd9-ede09994feb5')
        user = Advisor.objects.get(email='Ava.Walsh@example.com')
        contact = Contact.objects.get(email='archie@arakelian.com')
        serializer = OrderAssigneeSerializer(
            many=True,
            data=[{'adviser': {'id': 'b4848b30-f532-4cfc-a063-b064d8435b65'},
                   'estimated_time': 6000, 'is_lead': True}],
            context={
                'order': order,
                'modified_by': user,
                'force_delete': False,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        order.generate_quote(user, True)

        order.accept_quote(by=contact)
        Payment.objects.filter(order=order).delete()

        order.mark_as_paid(by=user, payments_data=[
            {
                'amount': 50000,
                'method': 'bacs',
                'received_on': date.today(),
            },
            {
                'amount': 50000,
                'method': 'manual',
                'received_on': date.today(),
            },
        ])
