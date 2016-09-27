"""Company models."""

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from core.models import BaseConstantModel, BaseModel


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BusinessType(BaseConstantModel):
    """Company business type."""
    pass


class Sector(BaseConstantModel):
    """Company sector."""
    pass


class EmployeeRange(BaseConstantModel):
    """Company employee range."""
    pass


class TurnoverRange(BaseConstantModel):
    """Company turnover range."""
    pass


class UKRegion(BaseConstantModel):
    """UK region."""
    pass


class Country(BaseConstantModel):
    """Country."""
    pass


class CompanyAbstract(BaseModel):
    """Share as much as possible in the company representation."""

    company_number = models.CharField(max_length=MAX_LENGTH, null=True, db_index=True)
    name = models.CharField(max_length=MAX_LENGTH, null=True)
    address_1 = models.CharField(max_length=MAX_LENGTH, null=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, null=True)
    address_town = models.CharField(max_length=MAX_LENGTH, null=True)
    address_county = models.CharField(max_length=MAX_LENGTH, null=True)
    address_country = models.CharField(max_length=MAX_LENGTH, null=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, null=True)
    address_care_of = models.CharField(max_length=MAX_LENGTH, null=True)
    po_box = models.CharField(max_length=MAX_LENGTH, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Company(CompanyAbstract):
    """Representation of the company as per CDMS.

    This is a read-only model and any saving operation should be prevented.
    It can't be an unmanaged model because Django is in charge of creating the schema and the migrations.
    """

    id = models.UUIDField(primary_key=True, db_index=True)
    business_type = models.ForeignKey('BusinessType', null=True)
    sector = models.ForeignKey('Sector', null=True)
    website = models.URLField(null=True)
    country = models.ForeignKey('Country', null=True)
    employee_range = models.ForeignKey('EmployeeRange', null=True)
    turnover_range = models.ForeignKey('TurnoverRange', null=True)
    uk_region = models.ForeignKey('UKRegion', null=True)
    description = models.TextField(null=True)

    @cached_property
    def companies_house_data(self):
        """Get the companies house data based on company number."""
        result = {}
        if self.company_number:
            try:
                result = CompaniesHouseCompany.objects.get(company_number=self.company_number)
            except CompaniesHouseCompany.DoesNotExist:
                pass
        return result


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
        return self.name


class InteractionType(BaseConstantModel):
    """Interaction type."""
    pass


class Advisor(BaseConstantModel):
    """Advisor."""
    pass


class Interaction(BaseModel):
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


class Title(BaseConstantModel):
    """Contact title."""
    pass


class Role(BaseConstantModel):
    """Contact role."""
    pass


class Contact(BaseModel):
    """Contact from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    title = models.ForeignKey('Title', null=True)
    name = models.CharField(max_length=MAX_LENGTH, null=True)
    role = models.ForeignKey('Role', null=True)
    phone = models.CharField(max_length=MAX_LENGTH, null=True)
    email = models.EmailField(null=True)
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
        return self.name
