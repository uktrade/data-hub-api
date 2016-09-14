"""Company models."""

from django.conf import settings
from django.db import models

from core.models import BaseConstantModel, BaseModel
from core.mixins import ReadOnlyModelMixin


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BusinessType(ReadOnlyModelMixin, BaseConstantModel):
    pass


class Sector(ReadOnlyModelMixin, BaseConstantModel):
    pass


class EmployeeRange(ReadOnlyModelMixin, BaseConstantModel):
    pass


class TurnoverRange(ReadOnlyModelMixin, BaseConstantModel):
    pass


class UKRegion(ReadOnlyModelMixin, BaseConstantModel):
    pass


class Country(ReadOnlyModelMixin, BaseConstantModel):
    pass


class Company(ReadOnlyModelMixin, BaseModel):
    """Representation of the company as per CDMS.

    This is a read-only model and any saving operation should be prevented.
    It can't be an unmanaged model because Django is in charge of creating the schema and the migrations.
    """

    id = models.UUIDField(primary_key=True, db_index=True)
    company_number = models.CharField(max_length=MAX_LENGTH, blank=True, db_index=True)
    uk_based = models.BooleanField(default=True)
    business_type = models.ForeignKey('BusinessType', null=False)
    trading_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    sector = models.ForeignKey('Sector', null=True)
    website = models.URLField(blank=True)
    country = models.ForeignKey('Country', null=True)
    employee_range = models.ForeignKey('EmployeeRange', null=True)
    turnover_range = models.ForeignKey('TurnoverRange', null=True)
    trading_address_1 = models.CharField(max_length=MAX_LENGTH, null=True)
    trading_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_country = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)
    uk_region = models.ForeignKey('UKRegion', null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.registered_name


class CompanyHouseCompany(ReadOnlyModelMixin, BaseModel):
    """Representation of Company House company."""

    company_number = models.CharField(max_length=MAX_LENGTH, primary_key=True, db_index=True)
    company_name = models.CharField(max_length=MAX_LENGTH)
    registered_address_care_of = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_po_box = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_country = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)
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
    pass


class Advisor(ReadOnlyModelMixin, BaseConstantModel):
    pass


class Interaction(ReadOnlyModelMixin, BaseModel):
    """Interaction from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    interaction_type = models.ForeignKey('InteractionType', null=True)
    subject = models.TextField(blank=True)
    date_of_interaction = models.DateTimeField(null=False)
    advisor = models.ForeignKey('Advisor', null=True)
    notes = models.TextField(blank=True)
    company = models.ForeignKey('Company', null=True)
    contact = models.ForeignKey('Contact', null=True)

    def __str__(self):
        return self.subject


class Title(ReadOnlyModelMixin, BaseConstantModel):
    pass


class Role(ReadOnlyModelMixin, BaseConstantModel):
    pass


class Contact(ReadOnlyModelMixin, BaseModel):
    """Contact from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True)
    title = models.ForeignKey('Title', null=True)
    first_name = models.CharField(max_length=MAX_LENGTH, blank=False)
    last_name = models.CharField(max_length=MAX_LENGTH, blank=False)
    role = models.ForeignKey('Role', null=True)
    phone = models.CharField(max_length=MAX_LENGTH, blank=True)
    email = models.EmailField(null=True, blank=True)
    address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_country = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)
    alt_phone = models.CharField(max_length=MAX_LENGTH, blank=True)
    alt_email = models.EmailField(null=True)
    notes = models.TextField(blank=True)
    company = models.ForeignKey('Company', null=True)
    primary_contact_team = models.TextField(blank=True)

    def __str__(self):
        return "{name} {surname}".format(name=self.first_name, surname=self.last_name)
