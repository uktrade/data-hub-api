import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core.models import BaseModel
from datahub.omis.quote.managers import QuoteManager


class TermsAndConditions(models.Model):
    """
    Terms an conditions for the quote.

    When a quote is created, the latest (-created_on:first) version of
    terms and conditions should be used.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_on = models.DateTimeField(
        db_index=True, auto_now_add=True,
        help_text='Set automatically.',
    )
    name = models.CharField(
        max_length=100,
        help_text='Only used internally.',
    )
    content = models.TextField(
        help_text=(
            'In <a href="https://daringfireball.net/projects/markdown/syntax">Markdown</a>. '
            'You can preview the formatted content using an online editor '
            'such as <a href="https://dillinger.io/">dillinger.io</a>'
        ),
    )

    class Meta:
        ordering = ('-created_on', )
        verbose_name_plural = 'terms and conditions'

    def __str__(self):
        """Human-readable representation"""
        return self.name


class Quote(BaseModel):
    """Details of a quote."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference = models.CharField(max_length=100)
    content = models.TextField()
    terms_and_conditions = models.ForeignKey(
        TermsAndConditions,
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    cancelled_on = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    accepted_on = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        'company.Contact',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    expires_on = models.DateField()

    objects = QuoteManager()

    def cancel(self, by):
        """
        Cancel the current quote.

        :param by: the adviser who is cancelling the quote
        """
        if self.is_cancelled():  # already cancelled, skip
            return

        self.cancelled_on = now()
        self.cancelled_by = by
        self.save()

    def accept(self, by):
        """
        Accepts the current quote.

        :param by: the contact who is accepting the quote
        """
        assert not self.is_cancelled()

        if self.is_accepted():  # already cancelled, skip
            return

        self.accepted_on = now()
        self.accepted_by = by
        self.save()

    def is_cancelled(self):
        """
        :returns: True if this quote is cancelled, False otherwise.
        """
        return self.cancelled_on

    def is_accepted(self):
        """
        :returns: True if this quote has been accepted, False otherwise.
        """
        return self.accepted_on

    def __str__(self):
        """Human-readable representation"""
        return self.reference
