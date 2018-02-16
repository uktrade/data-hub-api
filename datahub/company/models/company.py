"""Company models."""
import uuid

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from datahub.core import constants
from datahub.core.models import ArchivableModel, BaseConstantModel, BaseModel
from datahub.core.utils import StrEnum
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class CompanyPermission(StrEnum):
    """Permission codename constants."""

    read_company = 'read_company'
    read_company_document = 'read_company_document'


class ExportExperienceCategory(BaseConstantModel):
    """Export experience category."""

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'export experience categories'


class CompanyAbstract(models.Model):
    """Share as much as possible in the company representation."""

    name = models.CharField(max_length=MAX_LENGTH)
    registered_address_1 = models.CharField(max_length=MAX_LENGTH)
    registered_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    registered_address_country = models.ForeignKey(
        metadata_models.Country,
        related_name="%(class)ss",  # noqa: Q000
        null=True,
        on_delete=models.SET_NULL
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name


class Company(ArchivableModel, BaseModel, CompanyAbstract):
    """Representation of the company as per CDMS."""

    TRADING_ADDRESS_VALIDATION_MAPPING = {
        'trading_address_1': {'required': True},
        'trading_address_2': {'required': False},
        'trading_address_town': {'required': True},
        'trading_address_county': {'required': False},
        'trading_address_postcode': {'required': False},
        'trading_address_country': {'required': True},
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference_code = models.CharField(max_length=MAX_LENGTH, blank=True)
    company_number = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    vat_number = models.CharField(max_length=MAX_LENGTH, blank=True)
    alias = models.CharField(
        max_length=MAX_LENGTH, blank=True, null=True, help_text='Trading name'
    )
    business_type = models.ForeignKey(
        metadata_models.BusinessType, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    sector = models.ForeignKey(
        metadata_models.Sector, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    employee_range = models.ForeignKey(
        metadata_models.EmployeeRange, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    turnover_range = models.ForeignKey(
        metadata_models.TurnoverRange, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    account_manager = models.ForeignKey(
        'Advisor', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='companies'
    )
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
    description = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=MAX_LENGTH, blank=True, null=True)
    uk_region = models.ForeignKey(
        metadata_models.UKRegion, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    trading_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_town = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    trading_address_country = models.ForeignKey(
        metadata_models.Country,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='company_trading_address_country'
    )
    trading_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    headquarter_type = models.ForeignKey(
        metadata_models.HeadquarterType, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    classification = models.ForeignKey(
        metadata_models.CompanyClassification, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    parent = models.ForeignKey(
        'self', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='children'
    )
    global_headquarters = models.ForeignKey(
        'self', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='subsidiaries',
    )
    one_list_account_owner = models.ForeignKey(
        'Advisor', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='one_list_owned_companies'
    )
    export_experience_category = models.ForeignKey(
        ExportExperienceCategory, blank=True, null=True, on_delete=models.SET_NULL,
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this company.'
    )

    class Meta:
        verbose_name_plural = 'companies'
        permissions = (
            (CompanyPermission.read_company.value, 'Can read company'),
            (CompanyPermission.read_company_document.value, 'Can read company document')
        )

    @property
    def uk_based(self):
        """Whether a company is based in the UK or not."""
        if not self.registered_address_country:
            return None

        united_kingdom_id = uuid.UUID(constants.Country.united_kingdom.value.id)
        return self.registered_address_country.id == united_kingdom_id

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

    def has_valid_trading_address(self):
        """Tells if Company has all required trading address fields defined."""
        field_mapping = self.TRADING_ADDRESS_VALIDATION_MAPPING

        return all(
            getattr(self, field) for field, rules in field_mapping.items() if rules['required']
        )


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

    class Meta:
        verbose_name_plural = 'Companies House companies'
        permissions = (('read_companieshousecompany', 'Can read companies house companies'),)
