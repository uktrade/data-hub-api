import uuid

from django.conf import settings
from django.db import models

from datahub.core import reversion
from datahub.core.models import (
    BaseModel,
    BaseOrderedConstantModel,
)
from datahub.core.utils import get_front_end_url

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class LargeCapitalOpportunity(BaseModel):
    """Large capital opportunity model."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    name = models.CharField(max_length=MAX_LENGTH)

    type = models.ForeignKey(
        'opportunity.OpportunityType',
        related_name='+',
        on_delete=models.PROTECT,
    )

    description = models.TextField()

    uk_region_locations = models.ManyToManyField(
        'metadata.UKRegion',
        related_name='+',
        blank=True,
        verbose_name='List of UK regions',
    )

    promoters = models.ManyToManyField(
        'company.Company',
        related_name='opportunities',
        blank=True,
        verbose_name='List of Promoters',
    )

    required_checks_conducted = models.ForeignKey(
        'investor_profile.RequiredChecksConducted',
        related_name='+',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    required_checks_conducted_by = models.ForeignKey(
        'company.Advisor',
        related_name='+',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    required_checks_conducted_on = models.DateField(null=True, blank=True)

    lead_dit_relationship_manager = models.ForeignKey(
        'company.Advisor',
        related_name='+',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    other_dit_contacts = models.ManyToManyField(
        'company.Advisor',
        related_name='+',
        blank=True,
        verbose_name='List of DIT contacts',
    )

    asset_classes = models.ManyToManyField(
        'investor_profile.AssetClassInterest',
        related_name='+',
        blank=True,
    )

    opportunity_value_type = models.ForeignKey(
        'opportunity.OpportunityValueType',
        related_name='+',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Type of opportunity value',
    )

    opportunity_value = models.DecimalField(
        blank=True, null=True, max_digits=19, decimal_places=0,
        help_text='Opportunity value (£)',
    )

    construction_risks = models.ManyToManyField(
        'investor_profile.ConstructionRisk',
        related_name='+',
        blank=True,
    )

    total_investment_sought = models.DecimalField(
        blank=True, null=True, max_digits=19, decimal_places=0,
        help_text='Total investment sought (£)',
    )

    current_investment_secured = models.DecimalField(
        blank=True, null=True, max_digits=19, decimal_places=0,
        help_text='Current investment secured (£)',
    )

    investment_types = models.ManyToManyField(
        'investor_profile.LargeCapitalInvestmentType',
        related_name='+',
        blank=True,
    )

    estimated_return_rate = models.ForeignKey(
        'investor_profile.ReturnRate',
        related_name='+',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    time_horizons = models.ManyToManyField(
        'investor_profile.TimeHorizon',
        related_name='+',
        blank=True,
    )

    investment_projects = models.ManyToManyField(
        'investment.InvestmentProject',
        related_name='opportunities',
        blank=True,
    )

    status = models.ForeignKey(
        'opportunity.OpportunityStatus',
        related_name='+',
        on_delete=models.PROTECT,
    )

    sources_of_funding = models.ManyToManyField(
        'opportunity.SourceOfFunding',
        related_name='+',
        blank=True,
    )

    funding_supporting_details = models.TextField(blank=True)

    dit_support_provided = models.BooleanField()

    reasons_for_abandonment = models.ManyToManyField(
        'opportunity.AbandonmentReason',
        related_name='+',
        blank=True,
    )

    why_abandoned = models.TextField(blank=True)
    why_suspended = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'large capital opportunities'
        permissions = (
            ('export_largecapitalopportunity', 'Can export large capital opportunity'),
        )

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)


class OpportunityStatus(BaseOrderedConstantModel):
    """Opportunity status metadata."""


class OpportunityType(BaseOrderedConstantModel):
    """Opportunity type metadata."""


class OpportunityValueType(BaseOrderedConstantModel):
    """Opportunity value type metadata."""


class AbandonmentReason(BaseOrderedConstantModel):
    """Abandonment reason metadata."""


class SourceOfFunding(BaseOrderedConstantModel):
    """Source of funding metadata."""
