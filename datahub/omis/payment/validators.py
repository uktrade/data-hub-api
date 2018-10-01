from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings


class ReconcilablePaymentsValidator:
    """
    Validator which checks that the specified payments data can be
    reconciled, that is, their sum is equal or greater than the order total.
    """

    message = 'The sum of the amounts has to be equal or greater than the order total.'

    def __init__(self):
        """Initialise the object."""
        self.order = None

    def set_order(self, order):
        """Set the order attr to the selected one."""
        self.order = order

    def __call__(self, data):
        """Validate that payments data can be reconciled."""
        if sum(item_data['amount'] for item_data in data) < self.order.total_cost:
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: self.message,
            })
