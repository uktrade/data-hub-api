"""Company models."""
import uuid

from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now
from model_utils import Choices
from mptt.fields import TreeForeignKey

from datahub.company.ch_constants import COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING
from datahub.core import constants, reversion
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations
from datahub.core.models import ArchivableModel, BaseConstantModel, BaseModel
from datahub.core.utils import get_front_end_url, StrEnum
from datahub.metadata import models as metadata_models
from datahub.metadata.models import BusinessType

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class CompanyPermission(StrEnum):
    """Permission codename constants."""

    view_company = 'view_company'
    view_company_document = 'view_company_document'
    view_company_timeline = 'view_company_timeline'
    export_company = 'export_company'


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
        on_delete=models.SET_NULL,
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name


@reversion.register_base_model()
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
    TRANSFER_REASONS = Choices(
        ('duplicate', 'Duplicate record'),
    )
    ALLOWED_RELATIONS_FOR_MERGING = (
        ('company', 'Contact', 'company'),
        ('interaction', 'Interaction', 'company'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference_code = models.CharField(max_length=MAX_LENGTH, blank=True)
    company_number = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    vat_number = models.CharField(max_length=MAX_LENGTH, blank=True)
    alias = models.CharField(
        max_length=MAX_LENGTH, blank=True, null=True, help_text='Trading name',
    )
    business_type = models.ForeignKey(
        metadata_models.BusinessType, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    sector = TreeForeignKey(
        metadata_models.Sector, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    employee_range = models.ForeignKey(
        metadata_models.EmployeeRange, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    turnover_range = models.ForeignKey(
        metadata_models.TurnoverRange, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    export_to_countries = models.ManyToManyField(
        metadata_models.Country,
        blank=True,
        related_name='company_export_to_countries',
    )
    future_interest_countries = models.ManyToManyField(
        metadata_models.Country,
        blank=True,
        related_name='company_future_interest_countries',
    )
    description = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=MAX_LENGTH, blank=True, null=True)
    uk_region = models.ForeignKey(
        metadata_models.UKRegion, blank=True, null=True,
        on_delete=models.SET_NULL,
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
        related_name='company_trading_address_country',
    )
    trading_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    headquarter_type = models.ForeignKey(
        metadata_models.HeadquarterType, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    classification = models.ForeignKey(
        metadata_models.CompanyClassification, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    global_headquarters = models.ForeignKey(
        'self', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='subsidiaries',
    )
    one_list_account_owner = models.ForeignKey(
        'Advisor', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='one_list_owned_companies',
        help_text='Global account manager',
    )
    export_experience_category = models.ForeignKey(
        ExportExperienceCategory, blank=True, null=True, on_delete=models.SET_NULL,
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this company.',
    )
    transferred_to = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transferred_from',
        help_text='Where data about this company was transferred to.',
    )
    transfer_reason = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        choices=TRANSFER_REASONS,
        help_text='The reason data for this company was transferred.',
    )
    transferred_on = models.DateTimeField(blank=True, null=True)
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    class Meta:
        verbose_name_plural = 'companies'
        permissions = (
            (CompanyPermission.view_company_document.value, 'Can view company document'),
            (CompanyPermission.view_company_timeline.value, 'Can view company timeline'),
            (CompanyPermission.export_company.value, 'Can export company'),
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
                    company_number=self.company_number,
                )
            except CompaniesHouseCompany.DoesNotExist:
                return None

    def has_valid_trading_address(self):
        """Tells if Company has all required trading address fields defined."""
        field_mapping = self.TRADING_ADDRESS_VALIDATION_MAPPING

        return all(
            getattr(self, field) for field, rules in field_mapping.items() if rules['required']
        )

    def mark_as_transferred(self, to, reason, user):
        """
        Marks a company record as having been transferred to another company record.

        This is used, for example, for marking a company as a duplicate record.
        """
        self.transfer_reason = reason
        self.transferred_by = user
        self.transferred_on = now()
        self.transferred_to = to

        display_reason = self.get_transfer_reason_display()

        archived_reason = (
            f'This record is no longer in use and its data has been transferred to {to} for the '
            f'following reason: {display_reason}.'
        )

        # Note: archive() saves the model instance
        self.archive(user, archived_reason)

    @property
    def is_valid_merge_target(self):
        """
        Returns whether it is OK for other companies to be merged into this one.

        This is in reference to merging duplicate records and is used by the duplicate company
        merge tool in the admin site.
        """
        return not self.archived

    @cached_property
    def is_valid_merge_source(self):
        """
        Returns whether this company is allowed to be merged into another company.

        This is in reference to merging duplicate records and is used by the duplicate company
        merge tool in the admin site.

        This checks whether there are any references to this object, other than those through
        the relations soecified in ALLOWED_RELATIONS_FOR_MERGING. It also checks if this object
        has any references to other companies. If any of either of those types of references
        exist, merging is not permitted.
        """
        relations = get_related_fields(Company)
        allowed_relations = {
            apps.get_model(app_label, model_name)._meta.get_field(field_name).remote_field
            for app_label, model_name, field_name in self.ALLOWED_RELATIONS_FOR_MERGING
        }

        for relation in relations:
            if relation in allowed_relations:
                continue

            relation_object_count = getattr(self, relation.name).count()
            if relation_object_count:
                return False

        self_referential_fields = get_self_referential_relations(Company)
        return not any(getattr(self, field.name) for field in self_referential_fields)


class CompanyCoreTeamMember(models.Model):
    """
    Adviser who is a member of the core team of a company.

    When a company is account managed, a core team is established.
    This usually includes:
    - one and only one global account manager
    - a local account manager from the country where the company is based
    - one or more local account managers from the country where the company
        is exporting to or investing in

    However, this layout is not always as strict.
    Other roles might exist and a single person can also have multiple roles.

    This team is called "core team" because it's official and does not change
    often. Usually, a wider team around a company is established as well.
    This team includes specialists and other advisers needed for short-term
    and more reactive support.

    Company.one_list_account_owner who represents the global account manager
    is kept on the company record for now even though it's in theory part of
    the core team.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='core_team_members',
    )
    adviser = models.ForeignKey(
        'company.Advisor', on_delete=models.CASCADE, related_name='core_team_memberships',
    )

    def __str__(self):
        """Human-readable representation."""
        return f'{self.adviser} - core team member of {self.company}'

    class Meta:
        unique_together = (
            ('company', 'adviser'),
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

    @cached_property
    def business_type(self):
        """The business type associated with the company category provided by Companies House."""
        business_type = COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING.get(
            self.company_category.lower(),
        )
        if business_type:
            return BusinessType.objects.get(pk=business_type.value.id)
        return None

    class Meta:
        verbose_name_plural = 'Companies House companies'
