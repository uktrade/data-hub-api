"""Company models."""
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now

from datahub.company.validators import RelaxedURLValidator
from datahub.core import constants
from datahub.core import fields as core_fields
from datahub.core.models import ArchivableModel, BaseModel
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class CompanyAbstract(BaseModel):
    """Share as much as possible in the company representation."""

    name = models.CharField(max_length=MAX_LENGTH)
    registered_address_1 = models.CharField(max_length=MAX_LENGTH)
    registered_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_3 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_4 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_country = models.ForeignKey(
        metadata_models.Country,
        related_name="%(class)ss",  # noqa: Q000
        null=True,
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    class Meta:  # noqa: D101
        abstract = True

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name

    def save(self, *args, **kwargs):
        """Override the Django save implementation to hook the custom validation."""
        self.clean()
        super().save(*args, **kwargs)


class Company(ArchivableModel, CompanyAbstract):
    """Representation of the company as per CDMS."""

    REQUIRED_TRADING_ADDRESS_FIELDS = (
        'trading_address_1',
        'trading_address_country',
        'trading_address_town'
    )

    company_number = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    alias = models.CharField(max_length=MAX_LENGTH, blank=True, null=True, help_text='Trading name')
    business_type = models.ForeignKey(metadata_models.BusinessType, null=True)
    sector = models.ForeignKey(metadata_models.Sector, null=True)
    employee_range = models.ForeignKey(metadata_models.EmployeeRange, null=True)
    turnover_range = models.ForeignKey(metadata_models.TurnoverRange, null=True)
    account_manager = models.ForeignKey('Advisor', null=True, related_name='companies')
    export_to_countries = models.ManyToManyField(
        metadata_models.Country,
        blank=True,
        related_name='company_export_to_countries'
    )
    future_interest_countries = models.ManyToManyField(
        metadata_models.Country,
        blank=True,
        related_name='company_future_interest_countries'
    )
    lead = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    website = models.CharField(max_length=MAX_LENGTH, validators=[RelaxedURLValidator], blank=True, null=True)
    uk_region = models.ForeignKey(metadata_models.UKRegion, null=True)
    trading_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_3 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_4 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_town = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_country = models.ForeignKey(
        metadata_models.Country,
        null=True,
        related_name='company_trading_address_country'
    )
    trading_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    headquarter_type = models.ForeignKey(metadata_models.HeadquarterType, blank=True, null=True)
    classification = models.ForeignKey(metadata_models.CompanyClassification, null=True)
    parent = models.ForeignKey('self', null=True, related_name='subsidiaries')
    one_list_account_owner = models.ForeignKey('Advisor', null=True, related_name='one_list_owned_companies')

    class Meta:  # noqa: D101
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
        """Trading address fields are not mandatory in the model definition.

        If any trading address field is supplied then address_1, town and
        country must also be provided.
        """
        any_trading_address_fields = any((
            self.trading_address_1,
            self.trading_address_2,
            self.trading_address_3,
            self.trading_address_4,
            self.trading_address_town,
            self.trading_address_county,
            self.trading_address_postcode,
            self.trading_address_country
        ))
        all_required_trading_address_fields = all(getattr(self, field)
                                                  for field in self.REQUIRED_TRADING_ADDRESS_FIELDS)
        if any_trading_address_fields and not all_required_trading_address_fields:
            return False
        return True

    def _generate_trading_address_errors(self):
        """Generate per field error."""
        empty_fields = [field for field in self.REQUIRED_TRADING_ADDRESS_FIELDS if not getattr(self, field)]
        return {field: ['This field may not be null.'] for field in empty_fields}

    def _validate_uk_region(self):
        """UK region is mandatory if it's a UK company."""
        if self.uk_based and not self.uk_region:
            return False
        return True

    def clean(self):
        """Custom validation."""
        if not self._validate_trading_address():
            raise ValidationError(
                self._generate_trading_address_errors(),
            )
        if not self._validate_uk_region():
            raise ValidationError(
                {'uk_region': ['UK region is required for UK companies.']}
            )
        super(Company, self).clean()


class CompaniesHouseCompany(CompanyAbstract):
    """Representation of Companies House company."""

    company_number = models.CharField(max_length=MAX_LENGTH, unique=True)
    company_category = models.CharField(max_length=MAX_LENGTH, blank=True)
    company_status = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_3 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_4 = models.CharField(max_length=MAX_LENGTH, blank=True)
    uri = models.CharField(max_length=MAX_LENGTH, blank=True)
    incorporation_date = models.DateField(null=True)

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name

    class Meta:  # noqa: D101
        verbose_name_plural = 'Companies House companies'


class Contact(ArchivableModel, BaseModel):
    """Contact from CDMS."""

    REQUIRED_ADDRESS_FIELDS = (
        'address_1',
        'address_country',
        'address_town'
    )

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    title = models.ForeignKey(metadata_models.Title, blank=True, null=True)
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    job_title = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    company = models.ForeignKey('Company', related_name='contacts', null=True, blank=True)
    advisor = models.ForeignKey('Advisor', related_name='contacts', null=True, blank=True)
    primary = models.BooleanField()
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
    address_country = models.ForeignKey(metadata_models.Country, null=True, blank=True)
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    telephone_alternative = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    email_alternative = models.EmailField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    contactable_by_dit = models.BooleanField(default=False)
    contactable_by_dit_partners = models.BooleanField(default=False)
    contactable_by_email = models.BooleanField(default=True)
    contactable_by_phone = models.BooleanField(default=True)

    @cached_property
    def name(self):
        """Need this for ES."""
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name

    def _generate_address_errors(self):
        """Generate per field error."""
        empty_fields = [field for field in self.REQUIRED_ADDRESS_FIELDS if not getattr(self, field)]
        return {field: ['This field may not be null.'] for field in empty_fields}

    def validate_contact_preferences(self):
        """At least one of the contract preferences must be set to True."""
        if not self.contactable_by_email and not self.contactable_by_phone:
            error_message = 'A contact should have at least one way of being contacted. ' \
                            'Please select either email or phone, or both'
            raise ValidationError({'contactable_by_email': [error_message],
                                   'contactable_by_phone': [error_message]})

    def validate_address(self):
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
        all_required_fields_existence = all(getattr(self, field) for field in self.REQUIRED_ADDRESS_FIELDS)
        if self.address_same_as_company and some_address_fields_existence:
            error_message = 'Please select either address_same_as_company or enter an address manually, not both!'
            raise ValidationError({'address_same_as_company': error_message})
        if not self.address_same_as_company:
            if some_address_fields_existence and not all_required_fields_existence:
                raise ValidationError(self._generate_address_errors())
            elif not some_address_fields_existence:
                error_message = 'Please select either address_same_as_company or enter an address manually.'
                raise ValidationError({'address_same_as_company': error_message})

    def clean(self):
        """Custom validation."""
        self.validate_address()
        self.validate_contact_preferences()
        super(Contact, self).clean()

    def save(self, *args, **kwargs):
        """Override the Django save implementation to hook the custom validation."""
        self.clean()
        super().save(*args, **kwargs)


class AdvisorManager(BaseUserManager):
    """Django user manager made friendly to not having username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Creates and saves a User with the given username, email and password."""
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create super user."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class Advisor(AbstractBaseUser, PermissionsMixin):
    """Advisor."""

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    last_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    email = core_fields.CICharField(max_length=MAX_LENGTH, unique=True)  # CDMS users may not have tld
    dit_team = models.ForeignKey(metadata_models.Team, null=True)
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text=(
            'Designates whether this user should be treated as active. '
            'Deselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField('date joined', default=now)
    enabled = models.BooleanField(default=False)

    objects = AdvisorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @cached_property
    def name(self):
        """Full name shorthand."""
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name

    # Django User methods, required for Admin interface

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        return self.name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Sends an email to this User."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
