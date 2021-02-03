import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from datahub.core import reversion
from datahub.core.models import (
    BaseModel,
    BaseOrderedConstantModel,
)
from datahub.core.utils import get_front_end_url


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class LargeCapitalInvestorProfile(BaseModel):
    """Large capital investor profile model."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    investor_company = models.ForeignKey(
        'company.Company',
        related_name='investor_profiles',
        on_delete=models.CASCADE,
    )

    investor_type = models.ForeignKey(
        'investor_profile.InvestorType',
        related_name='+',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    investable_capital = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='Investable capital amount in USD',
        validators=[MinValueValidator(0)],
    )

    global_assets_under_management = models.BigIntegerField(
        blank=True,
        null=True,
        help_text='Global assets under management amount in USD',
        validators=[MinValueValidator(0)],
    )

    investor_description = models.TextField(
        blank=True,
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

    deal_ticket_sizes = models.ManyToManyField(
        'investor_profile.DealTicketSize',
        related_name='+',
        blank=True,
    )

    asset_classes_of_interest = models.ManyToManyField(
        'investor_profile.AssetClassInterest',
        related_name='+',
        blank=True,
    )

    investment_types = models.ManyToManyField(
        'investor_profile.LargeCapitalInvestmentType',
        related_name='+',
        blank=True,
    )

    minimum_return_rate = models.ForeignKey(
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

    restrictions = models.ManyToManyField(
        'investor_profile.Restriction',
        related_name='+',
        blank=True,
    )

    construction_risks = models.ManyToManyField(
        'investor_profile.ConstructionRisk',
        related_name='+',
        blank=True,
    )

    minimum_equity_percentage = models.ForeignKey(
        'investor_profile.EquityPercentage',
        related_name='+',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    desired_deal_roles = models.ManyToManyField(
        'investor_profile.DesiredDealRole',
        related_name='+',
        blank=True,
    )

    uk_region_locations = models.ManyToManyField(
        'metadata.UKRegion',
        related_name='+',
        blank=True,
        verbose_name='possible UK regions',
    )

    other_countries_being_considered = models.ManyToManyField(
        'metadata.Country',
        related_name='+',
        blank=True,
        help_text='The other countries being considered for investment',
    )

    notes_on_locations = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name_plural = 'large capital profiles'
        permissions = (
            ('export_largecapitalinvestorprofile', 'Can export large capital investor profiles'),
        )

    def __str__(self):
        """Human-readable representation"""
        return f'{self.investor_company}, Large capital profile'

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    @property
    def country_of_origin(self):
        """Returns the country of which the investment would originate from."""
        if self.investor_company:
            return self.investor_company.address_country


class InvestorType(BaseOrderedConstantModel):
    """Investor type metadata."""


class DealTicketSize(BaseOrderedConstantModel):
    """Deal ticket size metadata."""


class LargeCapitalInvestmentType(BaseOrderedConstantModel):
    """Large capital investment type metadata."""


class ReturnRate(BaseOrderedConstantModel):
    """Return rate metadata."""


class TimeHorizon(BaseOrderedConstantModel):
    """Investor time horizons metadata."""


class Restriction(BaseOrderedConstantModel):
    """Investor restrictions metadata."""


class ConstructionRisk(BaseOrderedConstantModel):
    """Investment construction risk metadata."""


class EquityPercentage(BaseOrderedConstantModel):
    """Equity percentage metadata."""


class DesiredDealRole(BaseOrderedConstantModel):
    """Desired deal role metadata."""


class RequiredChecksConducted(BaseOrderedConstantModel):
    """Required checks conducted metadata."""


class AssetClassInterestSector(BaseOrderedConstantModel):
    """Asset class interest sector metadata."""


class AssetClassInterest(BaseOrderedConstantModel):
    """Asset class interest metadata."""

    asset_class_interest_sector = models.ForeignKey(
        AssetClassInterestSector,
        related_name='asset_class_interests',
        on_delete=models.CASCADE,
    )
