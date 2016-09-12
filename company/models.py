"""Company models."""

from django.db import models
from model_utils.models import TimeStampedModel

from core.mixins import ReadOnlyModelMixin


class Company(ReadOnlyModelMixin, TimeStampedModel):
    """Representation of the company as per CDMS.

    This is a read-only model and any saving operation should be prevented.
    It can't be an unmanaged model because Django is in charge of creating the schema and the migrations.
    """

    id = models.UUIDField(primary_key=True, db_index=True)
    company_number = models.CharField(max_length=8, blank=True, db_index=True)
    uk_based = models.BooleanField(default=True)
    business_type = models.CharField(max_length=160, blank=False)
    registered_name = models.CharField(max_length=160, blank=False)
    trading_name = models.CharField(max_length=160, blank=True)
    sectors = models.TextField(blank=True)
    website = models.URLField(blank=True)
    number_of_employees = models.CharField(max_length=20, blank=True)
    annual_turnover = models.BigIntegerField(null=True, blank=True)
    trading_address_1 = models.CharField(max_length=300, null=True)
    trading_address_2 = models.CharField(max_length=300, blank=True)
    trading_address_town = models.CharField(max_length=50, blank=True)
    trading_address_county = models.CharField(max_length=50, blank=True)
    trading_address_country = models.CharField(max_length=100, blank=True)
    trading_address_postcode = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=50, blank=True)
    account_manager = models.CharField(max_length=100, blank=True)
    countries_of_interest = models.TextField(blank=True)
    currently_exporting_to = models.TextField(blank=True)
    connections = models.CharField(max_length=200, blank=True)
    business_description = models.TextField(blank=True)

    def __str__(self):
        return self.registered_name


class CompanyHouseCompany(ReadOnlyModelMixin, TimeStampedModel):
    """Representation of Company House company."""

    company_number = models.CharField(max_length=8, primary_key=True, db_index=True)
    company_name = models.CharField(max_length=160)
    registered_address_care_of = models.CharField(max_length=100, blank=True)
    registered_address_po_box = models.CharField(max_length=10, blank=True)
    registered_address_address_1 = models.CharField(max_length=300, blank=True)
    registered_address_address_2 = models.CharField(max_length=300, blank=True)
    registered_address_town = models.CharField(max_length=50, blank=True)
    registered_address_county = models.CharField(max_length=50, blank=True)
    registered_address_country = models.CharField(max_length=100, blank=True)
    registered_address_postcode = models.CharField(max_length=20, blank=True)
    company_category = models.CharField(max_length=100, blank=True)
    company_status = models.CharField(max_length=70, blank=True)
    sic_code_1 = models.CharField(max_length=170, blank=True)
    sic_code_2 = models.CharField(max_length=170, blank=True)
    sic_code_3 = models.CharField(max_length=170, blank=True)
    sic_code_4 = models.CharField(max_length=170, blank=True)
    uri = models.CharField(max_length=100, blank=True)
    incorporation_date = models.DateField(null=True)

    def __str__(self):
        return self.company_name


class Interaction(ReadOnlyModelMixin, TimeStampedModel):
    """Interaction from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    interaction_type = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    date_of_interaction = models.DateField(null=False)
    advisor = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    company = models.ForeignKey('Company', related_name="interactions")
    contact = models.ForeignKey('Contact', related_name="interactions")

    def __str__(self):
        return self.subject


class Contact(ReadOnlyModelMixin, TimeStampedModel):
    """Contact from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    title = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    role = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(null=True, blank=True)
    address_1 = models.CharField(max_length=300, blank=True)
    address_2 = models.CharField(max_length=300, blank=True)
    address_town = models.CharField(max_length=50, blank=True)
    address_county = models.CharField(max_length=50, blank=True)
    address_country = models.CharField(max_length=100, blank=True)
    address_postcode = models.CharField(max_length=20, blank=True)
    alt_phone = models.CharField(max_length=30, blank=True)
    alt_email = models.EmailField(null=True)
    notes = models.TextField(blank=True)
    company = models.ForeignKey('Company', null=True, related_name="contacts")
    primary_contact_team = models.TextField(blank=True)

    def __str__(self):
        return "{name} {surname}".format(name=self.first_name, surname=self.last_name)
