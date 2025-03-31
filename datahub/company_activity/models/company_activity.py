import uuid

from django.conf import settings
from django.db import models

from datahub.core import reversion

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class CompanyActivity(models.Model):
    """Representation of a company and its related activities (interactions, events,
    investments, referrals etc).

    This is to be used with OpenSearch so we can view, filter and sort all activities
    related to a company.

    The save methods of the related activities have been overwritten to write to this
    model as well.
    """

    class ActivitySource(models.TextChoices):
        """The type of activity, whether its an interaction, referral, event, investment etc"""

        interaction = ('interaction', 'interaction')
        referral = ('referral', 'referral')
        event = ('event', 'event')
        investment = ('investment', 'investment')
        order = ('order', 'order')
        great_export_enquiry = ('great_export_enquiry', 'great_export_enquiry')
        eyb_lead = ('eyb_lead', 'eyb_lead')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    company = models.ForeignKey(
        'company.Company',
        related_name='activities',
        on_delete=models.CASCADE,
    )
    activity_source = models.CharField(
        max_length=MAX_LENGTH,
        choices=ActivitySource.choices,
        help_text=(
            'The type of company activity, such as an interaction, event, referral etc.'
        ),
    )
    date = models.DateTimeField(
        help_text=(
            'A date field copied from the activity_source model, '
            'so it can be sorted in the API.'
        ),
    )

    # A single company activity must have one of the following relationships, but not multiple.
    interaction = models.ForeignKey(
        'interaction.Interaction',
        unique=True,
        null=True,
        blank=True,
        related_name='activity',
        on_delete=models.CASCADE,
        help_text=(
            'If related to an Interaction, must not have relations to any other activity '
            '(referral, event etc)'
        ),
    )
    referral = models.ForeignKey(
        'company_referral.CompanyReferral',
        unique=True,
        null=True,
        blank=True,
        related_name='activity',
        on_delete=models.CASCADE,
        help_text=(
            'If related to a CompanyReferral, must not have relations to any other activity '
            '(interaction, event etc)'
        ),
    )
    investment = models.ForeignKey(
        'investment.InvestmentProject',
        unique=True,
        null=True,
        blank=True,
        related_name='activity',
        on_delete=models.CASCADE,
        help_text=(
            'InvestmentProject for a company, must not have relations to any other activity '
            '(interaction, event etc)'
        ),
    )
    order = models.ForeignKey(
        'order.Order',
        unique=True,
        null=True,
        blank=True,
        related_name='activity',
        on_delete=models.CASCADE,
        help_text=(
            'If related to an omis Order, must not have relations to any other activity '
            '(referral, event etc)'
        ),
    )

    great_export_enquiry = models.ForeignKey(
        'company_activity.GreatExportEnquiry',
        unique=True,
        null=True,
        blank=True,
        related_name='activity',
        on_delete=models.CASCADE,
        help_text=(
            'If related to an great export enquiry, must not have relations to any other activity '
            '(referral, event etc)'
        ),
    )

    eyb_lead = models.ForeignKey(
        'investment_lead.EYBLead',
        unique=True,
        null=True,
        blank=True,
        related_name='activity',
        on_delete=models.CASCADE,
        help_text=(
            'If related to an EYB lead, must not have relations to any other activity '
            '(referral, event etc)'
        ),
    )

    def __str__(self):
        """Readable name for CompanyActivity"""
        return f'Activity from "{self.activity_source}" for company: {self.company.name}'
