import uuid

from django.db import models

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.core import reversion
from datahub.core.models import BaseModel


@reversion.register_base_model()
class PromptPayments(BaseModel):
    """Stores prompt payments data for companies, ingested from S3."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    source_id = models.BigIntegerField(unique=True, db_index=True)

    reporting_period_start_date = models.DateField()
    reporting_period_end_date = models.DateField()
    filing_date = models.DateField(db_index=True)

    # stores the raw company house number from the s3 data file
    company_name = models.TextField()
    company_house_number = models.TextField(db_index=True)
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='prompt_payments',
    )

    # stores the raw email address from the s3 data file
    email_address = models.TextField(db_index=True)
    contact = models.ForeignKey(
        Contact,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='prompt_payments',
    )

    approved_by = models.TextField()
    qualifying_contracts_in_period = models.BooleanField()
    average_paid_days = models.IntegerField()
    paid_within_30_days_pct = models.IntegerField()
    paid_31_to_60_days_pct = models.IntegerField()
    paid_after_61_days_pct = models.IntegerField()
    paid_later_than_terms_pct = models.IntegerField()
    payment_shortest_period_days = models.IntegerField()
    payment_longest_period_days = models.IntegerField()
    payment_max_period_days = models.IntegerField()
    payment_terms_changed_comment = models.TextField()
    payment_terms_changed_notified_comment = models.TextField()
    code_of_practice = models.TextField()
    other_electronic_invoicing = models.BooleanField()
    other_supply_chain_finance = models.BooleanField()
    other_retention_charges_in_policy = models.BooleanField()
    other_retention_charges_in_past = models.BooleanField()

    class Meta:
        verbose_name = 'Prompt Payments Data'
        verbose_name_plural = 'Prompt Payments Data'
        indexes = [
            models.Index(fields=['company', 'filing_date']),
            models.Index(fields=['reporting_period_start_date']),
            models.Index(fields=['reporting_period_end_date']),
        ]
        ordering = ('-filing_date', '-reporting_period_end_date')

    def __str__(self):
        return (
            f'{self.company_name} ({self.company_house_number}) - '
            f'{self.reporting_period_start_date} to {self.reporting_period_end_date}'
        )
