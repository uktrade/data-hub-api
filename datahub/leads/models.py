import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import ArchivableModel, BaseModel
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BusinessLead(ArchivableModel, BaseModel):
    """Business lead model.

    A business lead is a precursor to a contact and/or company existing in
    Data Hub. Some leads will result in a company and/or contact being
    created by the user further down the line (though many will not).

    Initially, a business lead is created with a company name (if known)
    and not linked to a company. It may then later be linked to a company
    via the company foreign key.
    """

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    last_name = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    job_title = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    company_name = models.CharField(max_length=MAX_LENGTH, null=True,
                                    blank=True)
    trading_name = models.CharField(max_length=MAX_LENGTH, null=True,
                                    blank=True)
    company = models.ForeignKey('company.Company', null=True, blank=True,
                                related_name='business_leads')
    advisor = models.ForeignKey('company.Advisor', null=True, blank=True,
                                related_name='business_leads')
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
                                        blank=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True,
                                        null=True)
    telephone_alternative = models.CharField(max_length=MAX_LENGTH,
                                             blank=True, null=True)
    email_alternative = models.EmailField(null=True, blank=True)
    contactable_by_dit = models.BooleanField(default=False)
    contactable_by_dit_partners = models.BooleanField(default=False)
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
