import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import ArchivableModel, BaseModel
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BusinessLead(ArchivableModel, BaseModel):
    """Business lead model.

    A business lead is early form of a contact and/or company. Some leads
    will result in a company and/or contact being created by the user
    further down the line (though many will not).

    Initially, a business lead is created with the name of a person or
    company. It may then later be linked to a company via the company
    foreign key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    last_name = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    job_title = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    company_name = models.CharField(max_length=MAX_LENGTH, null=True,
                                    blank=True)
    trading_name = models.CharField(max_length=MAX_LENGTH, null=True,
                                    blank=True)
    company = models.ForeignKey(
        'company.Company', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='business_leads'
    )
    telephone_number = models.CharField(max_length=MAX_LENGTH, null=True,
                                        blank=True)
    email = models.EmailField(null=True, blank=True)
    address_1 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_town = models.CharField(max_length=MAX_LENGTH, blank=True,
                                    null=True)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True,
                                      null=True)
    address_country = models.ForeignKey(metadata_models.Country, null=True,
                                        blank=True, on_delete=models.SET_NULL)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True,
                                        null=True)
    telephone_alternative = models.CharField(max_length=MAX_LENGTH,
                                             blank=True, null=True)
    email_alternative = models.EmailField(null=True, blank=True)

    # Marketing preferences
    contactable_by_dit = models.BooleanField(default=False)
    contactable_by_uk_dit_partners = models.BooleanField(default=False)
    contactable_by_overseas_dit_partners = models.BooleanField(default=False)
    accepts_dit_email_marketing = models.BooleanField(default=False)

    # Contact mode preferences
    contactable_by_email = models.BooleanField(default=False)
    contactable_by_phone = models.BooleanField(default=False)

    notes = models.TextField(null=True, blank=True)

    @property
    def name(self):
        """Formatted name."""
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        """Formatted name."""
        return self.name
