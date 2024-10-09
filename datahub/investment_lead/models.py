import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.validators import (
    integer_validator,
    MaxLengthValidator,
    MinLengthValidator,
)
from django.db import models
from mptt.fields import TreeForeignKey

from datahub.core.models import ArchivableModel


CHAR_FIELD_MAX_LENGTH = 256


class InvestmentLead(ArchivableModel):
    """Abstract model for different types of investment leads."""

    created_on = models.DateTimeField(db_index=True, null=True, blank=True, auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        abstract = True


class EYBLead(InvestmentLead):
    """Model for an Expand Your Business (EYB) investment lead.

    EYB leads come in two parts: triage and user data. This model represents a
    combination of both. The two data models can be joined on `*_hashed_uuid`.

    The fields in this model mirror those provided by the EYB endpoint.
    """

    class IntentChoices(models.TextChoices):
        SET_UP_NEW_PREMISES = 'SET_UP_NEW_PREMISES', 'Set up new premises'
        SET_UP_A_NEW_DISTRIBUTION_CENTRE = (
            'SET_UP_A_NEW_DISTRIBUTION_CENTRE',
            'Set up a new distribution centre',
        )
        ONWARD_SALES_AND_EXPORTS_FROM_THE_UK = (
            'ONWARD_SALES_AND_EXPORTS_FROM_THE_UK',
            'Onward sales and exports from the UK',
        )
        RESEARCH_DEVELOP_AND_COLLABORATE = (
            'RESEARCH_DEVELOP_AND_COLLABORATE',
            'Research, develop and collaborate',
        )
        FIND_PEOPLE_WITH_SPECIALIST_SKILLS = (
            'FIND_PEOPLE_WITH_SPECIALIST_SKILLS',
            'Find people with specialist skills',
        )
        OTHER = 'OTHER', 'Other'

    class HiringChoices(models.TextChoices):
        ONE_TO_FIVE = '1-5', '1 to 5'
        SIX_TO_FIFTY = '6-50', '6 to 50'
        FIFTY_ONE_TO_ONE_HUNDRED = '51-100', '51 to 100'
        ONE_HUNDRED_ONE_PLUS = '101+', 'More than 100'
        NO_PLANS_TO_HIRE_YET = 'NO_PLANS_TO_HIRE_YET', 'No plans to hire'

    class SpendChoices(models.TextChoices):
        LESS_THAN_TEN_THOUSAND = '0-9999', 'Less than £10,000'
        TEN_THOUSAND_TO_FIVE_HUNDRED_THOUSAND = '10000-500000', '£10,000 to £500,000'
        FIVE_HUNDRED_THOUSAND_TO_ONE_MILLION = '500000-1000000', '£500,000 to £1 million'
        ONE_MILLION_TO_TWO_MILLION = '1000000-2000000', '£1 million to £2 million'
        TWO_MILLION_TO_FIVE_MILLION = '2000000-5000000', '£2 million to £5 million'
        FIVE_MILLION_TO_TEN_MILLION = '5000000-10000000', '£5 million to £10 million'
        MORE_THAN_TEN_MILLION = '10000000+', 'More than £10 million'

    class LandingTimeframeChoices(models.TextChoices):
        UNDER_SIX_MONTHS = 'UNDER_SIX_MONTHS', 'In the next 6 months'
        SIX_TO_TWELVE_MONTHS = 'SIX_TO_TWELVE_MONTHS', '6 to 12 months'
        ONE_TO_TWO_YEARS = 'ONE_TO_TWO_YEARS', '1 to 2 years'
        OVER_TWO_YEARS = 'OVER_TWO_YEARS', "In more than 2 years' time"

    # EYB triage fields
    triage_hashed_uuid = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    triage_created = models.DateTimeField()
    triage_modified = models.DateTimeField()
    sector = TreeForeignKey(
        'metadata.Sector',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    sector_sub = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    intent = ArrayField(
        models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, choices=IntentChoices.choices),
        size=6,
        default=list,
    )
    intent_other = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    location = models.ForeignKey(
        'metadata.UKRegion',
        related_name='+',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    location_city = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    location_none = models.BooleanField(default=None, null=True)
    hiring = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, choices=HiringChoices.choices)
    spend = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, choices=SpendChoices.choices)
    spend_other = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    is_high_value = models.BooleanField(default=False)

    # EYB user fields
    user_hashed_uuid = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    user_created = models.DateTimeField()
    user_modified = models.DateTimeField()
    company_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    company_location = models.ForeignKey(
        'metadata.Country',
        related_name='+',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    full_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    role = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    email = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    telephone_number = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    agree_terms = models.BooleanField(default=False)
    agree_info_email = models.BooleanField(default=False)
    landing_timeframe = models.CharField(
        default='',
        max_length=CHAR_FIELD_MAX_LENGTH,
        blank=True,
        choices=LandingTimeframeChoices.choices,
    )
    company_website = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True,
    )

    # Company fields
    duns_number = models.CharField(
        blank=True,
        null=True,
        help_text='Dun & Bradstreet unique identifier. Nine-digit number with leading zeros.',
        max_length=9,
        validators=[
            MinLengthValidator(9),
            MaxLengthValidator(9),
            integer_validator,
        ],
    )
    address_1 = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    address_2 = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    address_town = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    address_county = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    address_area = models.ForeignKey(
        'metadata.AdministrativeArea',
        related_name='+',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    address_country = models.ForeignKey(
        'metadata.Country',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    address_postcode = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    company = models.ForeignKey(
        'company.Company',
        related_name='eyb_leads',
        help_text='Company associated with this EYB lead.',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    investment_project = models.ManyToManyField(
        'investment.InvestmentProject'
    )

    # UTM parameters
    utm_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    utm_source = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    utm_medium = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)
    utm_content = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True)

    def __str__(self):
        """String representation of the model."""
        return self.name

    @property
    def name(self):
        """The name of an EYB lead record."""
        shortened_pk = str(self.pk)[:8]
        if self.company:
            return f'EYB Lead ({shortened_pk}...) for {self.company.name}'
        return f'EYB Lead ({shortened_pk}...)'
