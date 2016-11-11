"""Company models."""
import uuid

from core import constants
from core.models import BaseConstantModel, BaseModel
from core.utils import model_to_dictionary
from dateutil import parser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils.functional import cached_property

from datahub.core.mixins import DeferredSaveModelMixin
from datahub.es import ESConnector

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
    registered_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_3 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_4 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_country = models.ForeignKey(
        'Country',
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Company(CompanyAbstract, BaseModel):
    """Representation of the company as per CDMS."""

    company_number = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    alias = models.CharField(max_length=MAX_LENGTH, blank=True, null=True, help_text='Trading name')
    business_type = models.ForeignKey('BusinessType')
    sector = models.ForeignKey('Sector')
    employee_range = models.ForeignKey('EmployeeRange', null=True)
    turnover_range = models.ForeignKey('TurnoverRange', null=True)
    account_manager = models.ForeignKey('Advisor', null=True)
    export_to_countries = models.ManyToManyField(
        'Country',
        blank=True,
        null=True,
        related_name='company_export_to_countries'
    )
    future_interest_countries = models.ManyToManyField(
        'Country',
        blank=True,
        null=True,
        related_name='company_future_interest_countries'
    )
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    uk_region = models.ForeignKey('UKRegion', null=True)
    trading_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_3 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_4 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_town = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_country = models.ForeignKey('Country', null=True, related_name='company_trading_address_country')
    trading_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'companies'

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

    def _validate_trading_address(self):
        """Trading address fields are not mandatory in the model definition, but
        if any trading address field is supplied then address_1, town and
        country must also be provided."""
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
            return False
        return True

    def _validate_uk_region(self):
        """UK region is mandatory if it's a UK company"""
        if self.uk_based and not self.uk_region:
            return False
        return True

    def clean(self):
        """Custom validation."""
        if not self._validate_trading_address():
            raise ValidationError(
                'If a trading address is specified, it must be complete.'
            )
        if not self._validate_uk_region():
            raise ValidationError(
                'UK region is required for UK companies.'
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


class Interaction(BaseModel):
    """Interaction from CDMS."""

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    interaction_type = models.ForeignKey('InteractionType', null=True)
    subject = models.TextField()
    date_of_interaction = models.DateTimeField()
    dit_advisor = models.ForeignKey('Advisor')
    notes = models.TextField()
    company = models.ForeignKey('Company', related_name='interactions')
    contact = models.ForeignKey('Contact', related_name='interactions')
    service = models.ForeignKey('Service')
    dit_team = models.ForeignKey('Team')

    def __str__(self):
        return self.subject

    def _map_korben_response_to_model_instance(self, korben_response):
        """Handle date field."""

        super(Interaction, self)._map_korben_response_to_model_instance(korben_response)
        date_of_interaction_string = korben_response.json().get('date_of_interaction')
        if date_of_interaction_string:
            self.date_of_interaction = parser.parse(date_of_interaction_string)

    def get_excluded_fields(self):
        """Don't send user to Korben, it's a Django thing."""
        return ['user']


class Title(BaseConstantModel):
    """Contact title."""
    pass


class Role(BaseConstantModel):
    """Contact role."""
    pass


class Team(BaseConstantModel):
    """Team."""
    pass


class Service(BaseConstantModel):
    """Service."""
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
    address_1 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_3 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_4 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_town = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_country = models.ForeignKey('Country', null=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    telephone_alternative = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    email_alternative = models.EmailField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    @cached_property
    def name(self):
        """Need this for ES."""
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    @cached_property
    def address(self):
        """Return the company address if the flag is selected."""
        address_country = None

        if self.address_same_as_company:
            if self.company.trading_address_country:
                address_country = {
                   'id': self.company.trading_address_country.pk,
                   'name': self.company.trading_address_country.name
                }
            else:
                address_country = {
                    'id':  self.company.registered_address_country.pk,
                    'name':  self.company.registered_address_country.name
                }

            return {
                'address_1': self.company.trading_address_1 or self.company.registered_address_1,
                'address_2': self.company.trading_address_2 or self.company.registered_address_2,
                'address_3': self.company.trading_address_3 or self.company.registered_address_3,
                'address_4': self.company.trading_address_4 or self.company.registered_address_4,
                'address_town': self.company.trading_address_town or self.company.registered_address_town,
                'address_country': address_country,
                'address_county': self.company.trading_address_county or self.company.registered_address_county,
                'address_postcode': self.company.trading_address_postcode or self.company.registered_address_postcode,
            }
        else:
            if self.address_country:
                address_country = {'id': self.address_country.pk , 'name': self.address_country.name}
            return {
                'address_1': self.address_1,
                'address_2': self.address_2,
                'address_3': self.address_3,
                'address_4': self.address_4,
                'address_town': self.address_town,
                'address_country': address_country,
                'address_county': self.address_county,
                'address_postcode': self.address_postcode,
            }

    def __str__(self):
        return self.name

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
        if self.address_same_as_company and some_address_fields_existence:
            raise ValidationError('Please select either address_same_as_company or enter an address manually, not both!')
        if not self.address_same_as_company:
            if some_address_fields_existence and not all_required_fields_existence:
                raise ValidationError('address_1, town and country are required if an address is entered.')
            elif not some_address_fields_existence:
                raise ValidationError('Please select either address_same_as_company or enter an address manually.')
        super(Contact, self).clean()


class Advisor(DeferredSaveModelMixin, models.Model):
    """Advisor."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    dit_team = models.ForeignKey('Team')
    email = models.EmailField()

    @cached_property
    def name(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def __str__(self):
        return self.name

    def get_excluded_fields(self):
        """Don't send user to Korben, it's a Django thing."""
        return ['user']


# Create a Django user when an advisor is created
def create_user_for_advisor(instance, created, **kwargs):
    if created and not instance.user:
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username=instance.email.split('@')[0],
            email=instance.email,
            first_name=instance.first_name,
            last_name=instance.last_name,
        )
        user.set_unusable_password()
        instance.user = user
        try:
            instance.save()
        except IntegrityError:  # somehow factories are saving it twice and it blows up, prevent it from happening
            pass


# Create an advisor when a user is created (ie using the shell)
# Users should be created through advisors, this covers the case of automated tests and users created with
# the management command
@receiver(post_save, sender=User)  # cannot use get_user_model() because app registry is not initialised
def create_advisor_for_user(instance, created, **kwargs):
    if created:
        advisor = Advisor(
            user=instance,
            first_name=instance.first_name if instance.first_name else instance.email,
            last_name=instance.last_name,
            dit_team=Team.objects.get(name='Undefined'),
            email=instance.email
        )
        advisor.save(as_korben=True)  # don't talk to Korben, this is not an Advisor we want to save in CDMS!


# Write to ES stuff
@receiver((post_save, m2m_changed))
def save_to_es(sender, instance, **kwargs):
    """Save to ES."""

    if sender in (Company, CompaniesHouseCompany, Contact, Interaction):
        es_connector = ESConnector()
        doc_type = type(instance)._meta.db_table  # cannot access _meta from the instance
        data = model_to_dictionary(instance)
        es_connector.save(doc_type=doc_type, data=data)
