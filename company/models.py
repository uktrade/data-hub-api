"""Company models."""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property

from core import constants
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


class CompanyAbstract(models.Model):
    """Share as much as possible in the company representation."""

    name = models.CharField(max_length=MAX_LENGTH)
    registered_address_1 = models.CharField(max_length=MAX_LENGTH)
    registered_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_3 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_4 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_country = models.ForeignKey(
        'Country',
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Company(CompanyAbstract, BaseModel):
    """Representation of the company as per CDMS."""

    company_number = models.CharField(max_length=MAX_LENGTH, null=True)
    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    alias = models.CharField(max_length=MAX_LENGTH, blank=True, help_text='Trading name')
    business_type = models.ForeignKey('BusinessType')
    sector = models.ForeignKey('Sector')
    employee_range = models.ForeignKey('EmployeeRange', null=True)
    turnover_range = models.ForeignKey('TurnoverRange', null=True)
    account_manager = models.ForeignKey('Advisor', null=True)
    export_to_countries = models.ManyToManyField(
        'Country',
        blank=True,
        related_name='company_export_to_countries'
    )
    future_interest_countries = models.ManyToManyField(
        'Country',
        blank=True,
        related_name='company_future_interest_countries'
    )
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    uk_region = models.ForeignKey('UKRegion')
    trading_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_3 = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_4 = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    trading_address_country = models.ForeignKey('Country', null=True, related_name='company_trading_address_country')
    trading_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

    @cached_property
    def uk_based(self):
        """Whether a company is based in the UK or not."""
        return self.registered_address_country.name == constants.Country.united_kingdom.value.name

    @cached_property
    def companies_house_data(self):
        """Get the companies house data based on company number."""
        if self.company_number:
            try:
                return CompaniesHouseCompany.objects.get(
                    company_number=self.company_number
                )
            except CompaniesHouseCompany.DoesNotExist:
                return None

    @cached_property
    def registered_name(self):
        """Use the CH name, if there's one, else the name."""
        return self.companies_house_data.name if self.companies_house_data else self.name

    def clean(self):
        """Custom validation for trading address.

        Trading address fields are not mandatory in the model definition, but
        if any trading address field is supplied then address_1, town and
        country must also be provided.
        """
        some_trading_address_fields = any((
            self.trading_address_1,
            self.trading_address_2,
            self.trading_address_3,
            self.trading_address_4,
            self.trading_address_town,
            self.trading_address_county,
            self.trading_address_postcode,
            self.trading_address_country
        ))
        trading_address_fields_missing = not all((
            self.trading_address_1,
            self.trading_address_country,
            self.trading_address_town
        ))
        if some_trading_address_fields and trading_address_fields_missing:
            raise ValidationError(
                'If a trading address is specified, it must be complete.'
            )
        super(Company, self).clean()


class CompaniesHouseCompany(CompanyAbstract):
    """Representation of Companies House company."""

    company_number = models.CharField(
        max_length=MAX_LENGTH,
        null=True,
        db_index=True,
        unique=True
    )
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

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    interaction_type = models.ForeignKey('InteractionType', null=True)
    subject = models.TextField(null=True)
    date_of_interaction = models.DateTimeField(null=True)
    advisor = models.ForeignKey('Advisor', null=True)
    notes = models.TextField(null=True)
    company = models.ForeignKey('Company', null=True, related_name='interactions')
    contact = models.ForeignKey('Contact', null=True, related_name='interactions')

    def __str__(self):
        return self.subject


class Title(BaseConstantModel):
    """Contact title."""
    pass


class Role(BaseConstantModel):
    """Contact role."""
    pass


class Team(BaseConstantModel):
    """Team."""
    pass


class Contact(BaseModel):
    """Contact from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    title = models.ForeignKey('Title')
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    role = models.ForeignKey('Role')
    company = models.ForeignKey('Company', related_name='contacts')
    primary = models.BooleanField()
    teams = models.ManyToManyField('Team', blank=True)
    telephone_countrycode = models.CharField(max_length=MAX_LENGTH)
    telephone_number = models.CharField(max_length=MAX_LENGTH)
    email = models.EmailField()
    address_same_as_company = models.BooleanField(default=False)
    address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_3 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_4 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_country = models.ForeignKey('Country', null=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)
    uk_region = models.ForeignKey('UKRegion')
    telephone_alternative = models.CharField(max_length=MAX_LENGTH, null=True)
    email_alternative = models.EmailField(null=True)
    notes = models.TextField(null=True)

    @cached_property
    def address(self):
        """Return the company address if the flag is selected."""

        if self.address_same_as_company:
            return {
                'address_1': self.company.trading_address_1 or self.company.registered_address_1,
                'address_2': self.company.trading_address_2 or self.company.registered_address_2,
                'address_3': self.company.trading_address_3 or self.company.registered_address_3,
                'address_4': self.company.trading_address_4 or self.company.registered_address_4,
                'address_town': self.company.trading_address_town or self.company.registered_address_town,
                'address_country': self.company.trading_address_country.pk if self.company.trading_address_country else self.company.registered_address_country.name,
                'address_county': self.company.trading_address_county or self.company.registered_address_county,
                'address_postcode': self.company.trading_address_postcode or self.company.registered_address_postcode,
            }
        else:
            return {
               'address_1': self.address_1,
               'address_2': self.address_2,
               'address_3': self.address_3,
               'address_4': self.address_4,
               'address_town': self.address_town,
               'address_country': self.address_country.pk,
               'address_county': self.address_county,
               'address_postcode': self.address_postcode,
            }

    def __str__(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def clean(self):
        """Custom validation for address.

        Either 'same_as_company' or address_1, address_town and address_country must be defined.
        """
        some_address_fields_existence = any((
                self.address_1,
                self.address_2,
                self.address_3,
                self.address_4,
                self.address_town,
                self.address_county,
                self.address_postcode,
                self.address_country
            ))
        all_required_fields_existence = all((
                self.address_1,
                self.address_country,
                self.address_town
            ))

        if not self.address_same_as_company:
            if some_address_fields_existence and not all_required_fields_existence:
                raise ValidationError('address_1, town and country are required if an address is entered.')
            elif not some_address_fields_existence:
                raise ValidationError('Please select either address_as_company or enter an address manually.')
        super(Contact, self).clean()
