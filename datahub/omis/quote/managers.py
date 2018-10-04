from django.db import models

from .utils import (
    calculate_quote_expiry_date,
    generate_quote_content,
    generate_quote_reference,
    get_latest_terms_and_conditions,
)


class QuoteManager(models.Manager):
    """Custom Quote Manager."""

    def create_from_order(self, order, by, commit=True):
        """
        :param order: Order instance for this quote
        :param by: who made the action
        :param commit: True if the changes have to be committed

        :returns: Quote object generated from the order
        """
        expires_on = calculate_quote_expiry_date(order)

        quote = self.model(
            reference=generate_quote_reference(order),
            content=generate_quote_content(order, expires_on),
            expires_on=expires_on,
            terms_and_conditions=get_latest_terms_and_conditions(),
        )

        if commit:
            quote.created_by = by
            quote.save()

        return quote
