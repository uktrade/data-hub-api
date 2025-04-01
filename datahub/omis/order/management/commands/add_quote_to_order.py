from django.core.management import BaseCommand

from datahub.company.models import Advisor
from datahub.omis.order.models import Order
from datahub.omis.order.serializers import OrderAssigneeSerializer


class Command(BaseCommand):
    """Command to complete the order creation process after initial test data added to database
    by adding an assignee to the order and generating the quote.
    Example of executing the command locally:
        python manage.py add_quote_to_order.
    """

    help = 'Complete order creation process once test data has been added to the database'

    def handle(self, *args, **options):
        """Adds assignee with the hours and making them the lead, and generates the quote."""
        user = Advisor.objects.get(email='Ava.Walsh@example.com')
        order = Order.objects.get(pk='59ad99d9-f589-4e5b-bea2-c1b0096671b7')
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
