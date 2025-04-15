import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.validators import (
    MaxLengthValidator,
    MinLengthValidator,
    integer_validator,
)
from django.db import models, transaction
from mptt.fields import TreeForeignKey

from datahub.company.models import Advisor
from datahub.company_activity.models import CompanyActivity
from datahub.core import reversion
from datahub.core.models import ArchivableModel

CHAR_FIELD_MAX_LENGTH = 256


class InvestmentLead(ArchivableModel):
    """Abstract model for different types of investment leads."""

    created_on = models.DateTimeField(db_index=True, null=True, blank=True, auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    advisers = models.ManyToManyField(
        Advisor,
        related_name='+',
    )

    class Meta:
        abstract = True


@reversion.register_base_model()
class EYBLead(InvestmentLead):
    """Model for an Expand Your Business (EYB) investment lead.

    EYB leads come in three parts: triage, user, and marketing data.
    This model represents a combination of these, but also contains additional Data Hub fields.

    The three data models can be joined on `*_hashed_uuid` which represent's the EYB
    user's unique ID.
    """

    # EYB triage fields
    triage_hashed_uuid = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    triage_created = models.DateTimeField(null=True, blank=True)
    triage_modified = models.DateTimeField(null=True, blank=True)
    # We will receive the fields: sectorId, sector, sectorSub, sectorSubSub from EYB
    # This can all be captured at creation as a single related field to a sector instance
    sector = TreeForeignKey(
        'metadata.Sector',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    sector_segments = ArrayField(
        models.CharField(max_length=CHAR_FIELD_MAX_LENGTH),
        size=3,
        default=list,
    )
    intent = ArrayField(
        models.CharField(max_length=CHAR_FIELD_MAX_LENGTH),
        size=6,
        default=list,
    )
    intent_other = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    # We receive location, locationCity, and locationNone from EYB;
    # These fields represent the proposed location of investment (i.e. UK region etc);
    # We have mapped and renamed the fields respectively, for clarity.
    proposed_investment_region = models.ForeignKey(
        'metadata.UKRegion',
        related_name='+',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    proposed_investment_city = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH,
        default='',
        blank=True,
    )
    proposed_investment_location_none = models.BooleanField(default=None, null=True, blank=True)
    hiring = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH,
        default='',
        blank=True,
    )
    spend = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH,
        default='',
        blank=True,
    )
    spend_other = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    is_high_value = models.BooleanField(default=None, null=True)

    # EYB user fields
    user_hashed_uuid = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    user_created = models.DateTimeField(null=True, blank=True)
    user_modified = models.DateTimeField(null=True, blank=True)
    company_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    duns_number = models.CharField(  # noqa: DJ001
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
    address_1 = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    address_2 = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    address_town = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    address_county = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    address_country = models.ForeignKey(
        'metadata.Country',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    address_postcode = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    company_website = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH,
        default='',
        blank=True,
    )
    full_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    role = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    email = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    telephone_number = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    agree_terms = models.BooleanField(default=None, null=True)
    agree_info_email = models.BooleanField(default=None, null=True)
    landing_timeframe = models.CharField(
        default='',
        max_length=CHAR_FIELD_MAX_LENGTH,
        blank=True,
    )

    # Related fields
    company = models.ForeignKey(
        'company.Company',
        related_name='eyb_leads',
        help_text='Company associated with this EYB lead.',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    investment_projects = models.ManyToManyField(
        'investment.InvestmentProject',
        related_name='eyb_leads',
        help_text='Investment Projects associated with this EYB lead.',
        null=True,
        blank=True,
    )

    # EYB marketing fields
    marketing_hashed_uuid = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH,
        default='',
        blank=True,
    )
    utm_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    utm_source = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    utm_medium = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)
    utm_content = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, default='', blank=True)

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

    def save(self, *args, **kwargs):
        """Creates a CompanyActivity when a EYB Lead is saved."""
        with transaction.atomic():
            super().save(*args, **kwargs)
            if not self.company:
                return
            CompanyActivity.objects.update_or_create(
                eyb_lead_id=self.id,
                activity_source=CompanyActivity.ActivitySource.eyb_lead,
                defaults={
                    'date': self.triage_created
                    if self.triage_created is not None
                    else self.created_on,
                    'company_id': self.company_id,
                },
            )
