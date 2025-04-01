from django.core.management import BaseCommand

from datahub.company.models import Advisor, Contact
from datahub.omis.order.models import Order
from datahub.omis.order.serializers import OrderAssigneeSerializer


class Command(BaseCommand):
    """Command to complete the order creation process after initial test data added to database
    by adding an assignee to the order, then generating and accepting a quote.
    Example of executing the command locally:
        python manage.py add_invoice_to_order.
    """

    help = 'Complete order creation process once test data has been added to the database'

    def handle(self, *args, **options):
        """Adds assignee with the hours and making them the lead, and generates the quote."""
        order = Order.objects.get(pk='00055b60-9bbe-4d59-8791-b2bceebf3881')
        user = Advisor.objects.get(email='Ava.Walsh@example.com')
        contact = Contact.objects.get(email='archie@arakelian.com')
        serializer = OrderAssigneeSerializer(
            many=True,
            data=[
                {
                    'adviser': {'id': 'b4848b30-f532-4cfc-a063-b064d8435b65'},
                    'estimated_time': 6000,
                    'is_lead': True,
                },
            ],
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
