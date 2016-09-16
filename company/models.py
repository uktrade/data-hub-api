"""Company models."""

from django.conf import settings
from django.db import models

from core.models import BaseConstantModel, BaseModel
from core.mixins import ReadOnlyModelMixin


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BusinessType(ReadOnlyModelMixin, BaseConstantModel):
    """Company business type."""
    pass


class Sector(ReadOnlyModelMixin, BaseConstantModel):
    """Company sector."""
    pass


class EmployeeRange(ReadOnlyModelMixin, BaseConstantModel):
    """Company employee range."""
    pass


class TurnoverRange(ReadOnlyModelMixin, BaseConstantModel):
    """Company turnover range."""
    pass


class UKRegion(ReadOnlyModelMixin, BaseConstantModel):
    """UK region."""
    pass


class Country(ReadOnlyModelMixin, BaseConstantModel):
    """Country."""
    pass


class CompanyAbstract(ReadOnlyModelMixin, BaseModel):
    """Share as much as possible in the company representation."""

    company_number = models.CharField(max_length=MAX_LENGTH, null=True, db_index=True)
    name = models.CharField(max_length=MAX_LENGTH, null=True)
    address_1 = models.CharField(max_length=MAX_LENGTH, null=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, null=True)
    address_town = models.CharField(max_length=MAX_LENGTH, null=True)
    address_county = models.CharField(max_length=MAX_LENGTH, null=True)
    address_country = models.CharField(max_length=MAX_LENGTH, null=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, null=True)
    address_care_of = models.CharField(max_length=MAX_LENGTH, blank=True)
    po_box = models.CharField(max_length=MAX_LENGTH, blank=True)

    class Meta:
        abstract = True


class Company(CompanyAbstract):
    """Representation of the company as per CDMS.

    This is a read-only model and any saving operation should be prevented.
    It can't be an unmanaged model because Django is in charge of creating the schema and the migrations.
    """

    id = models.UUIDField(primary_key=True, db_index=True)
    uk_based = models.NullBooleanField(default=True, null=True)
    business_type = models.ForeignKey('BusinessType', null=True)
    sector = models.ForeignKey('Sector', null=True)
    website = models.URLField(null=True)
    country = models.ForeignKey('Country', null=True)
    employee_range = models.ForeignKey('EmployeeRange', null=True)
    turnover_range = models.ForeignKey('TurnoverRange', null=True)
    uk_region = models.ForeignKey('UKRegion', null=True)
    description = models.TextField(null=True)

    def __str__(self):
        return self.registered_name


class CompaniesHouseCompany(CompanyAbstract):
    """Representation of Companies House company."""

    company_category = models.CharField(max_length=MAX_LENGTH, blank=True)
    company_status = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_3 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_4 = models.CharField(max_length=MAX_LENGTH, blank=True)
    uri = models.CharField(max_length=MAX_LENGTH, blank=True)
    incorporation_date = models.DateField(null=True)

    def __str__(self):
        return self.company_name


class InteractionType(ReadOnlyModelMixin, BaseConstantModel):
    """Interaction type."""
    pass


class Advisor(ReadOnlyModelMixin, BaseConstantModel):
    """Advisor."""
    pass


class Interaction(ReadOnlyModelMixin, BaseModel):
    """Interaction from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    interaction_type = models.ForeignKey('InteractionType', null=True)
    subject = models.TextField(null=True)
    date_of_interaction = models.DateTimeField(null=True)
    advisor = models.ForeignKey('Advisor', null=True)
    notes = models.TextField(null=True)
    company = models.ForeignKey('Company', null=True)
    contact = models.ForeignKey('Contact', null=True)

    def __str__(self):
        return self.subject


class Title(ReadOnlyModelMixin, BaseConstantModel):
    """Contact title."""
    pass


class Role(ReadOnlyModelMixin, BaseConstantModel):
    """Contact role."""
    pass


class Contact(ReadOnlyModelMixin, BaseModel):
    """Contact from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    title = models.ForeignKey('Title', null=True)
    first_name = models.CharField(max_length=MAX_LENGTH, null=True)
    last_name = models.CharField(max_length=MAX_LENGTH, null=True)
    role = models.ForeignKey('Role', null=True)
    phone = models.CharField(max_length=MAX_LENGTH, null=True)
    email = models.EmailField(null=True, blank=True)
    address_1 = models.CharField(max_length=MAX_LENGTH, null=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, null=True)
    address_town = models.CharField(max_length=MAX_LENGTH, null=True)
    address_county = models.CharField(max_length=MAX_LENGTH, null=True)
    address_country = models.CharField(max_length=MAX_LENGTH, null=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, null=True)
    alt_phone = models.CharField(max_length=MAX_LENGTH, null=True)
    alt_email = models.EmailField(null=True)
    notes = models.TextField(null=True)
    company = models.ForeignKey('Company', null=True)
    primary_contact_team = models.TextField(null=True)

    def __str__(self):
        return "{0} {1}".format(self.first_name, self.last_name)
