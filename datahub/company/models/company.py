"""Company models."""
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.validators import (
    integer_validator,
    MaxLengthValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now
from model_utils import Choices
from mptt.fields import TreeForeignKey

from datahub.company.ch_constants import COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING
from datahub.core import constants, reversion
from datahub.core.models import (
    ArchivableModel,
    BaseConstantModel,
    BaseModel,
    BaseOrderedConstantModel,
    DisableableModel,
)
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
    add_company = 'add_company'
    change_regional_account_manager = 'change_regional_account_manager'


class ExportExperienceCategory(BaseConstantModel):
    """Export experience category."""

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'export experience categories'


class OneListTier(BaseOrderedConstantModel):
    """One List tier."""


@reversion.register_base_model()
class Company(ArchivableModel, BaseModel):
    """Representation of the company."""

    TRANSFER_REASONS = Choices(
        ('duplicate', 'Duplicate record'),
    )

    EXPORT_POTENTIAL_SCORES = Choices(
        ('very_high', 'Very High'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('very_low', 'Very Low'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=MAX_LENGTH)
    reference_code = models.CharField(max_length=MAX_LENGTH, blank=True)
    company_number = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    vat_number = models.CharField(max_length=MAX_LENGTH, blank=True)
    duns_number = models.CharField(
        blank=True,
        null=True,
        help_text='Dun & Bradstreet unique identifier. Nine-digit number with leading zeros.',
        max_length=9,
        unique=True,
        validators=[
            MinLengthValidator(9),
            MaxLengthValidator(9),
            integer_validator,
        ],
    )
    trading_names = ArrayField(
        models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH),
        blank=True,
        default=list,
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
        help_text=(
            'Not used when duns_number is set. In that case, use number_of_employees instead.'
        ),
    )
    number_of_employees = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Only used when duns_number is set.',
    )
    is_number_of_employees_estimated = models.BooleanField(
        null=True,
        blank=True,
        help_text='Only used when duns_number is set.',
    )
    turnover_range = models.ForeignKey(
        metadata_models.TurnoverRange, blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text='Not used when duns_number is set. In that case, use turnover instead.',
    )
    turnover = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='In USD. Only used when duns_number is set.',
        validators=[MinValueValidator(0)],
    )
    is_turnover_estimated = models.BooleanField(
        null=True,
        blank=True,
        help_text='Only used when duns_number is set.',
    )
    export_to_countries = models.ManyToManyField(
        metadata_models.Country,
        blank=True,
        related_name='companies_exporting_to',
    )
    future_interest_countries = models.ManyToManyField(
        metadata_models.Country,
        blank=True,
        related_name='companies_with_future_interest',
    )
    description = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=MAX_LENGTH, blank=True, null=True)
    uk_region = models.ForeignKey(
        metadata_models.UKRegion, blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    # address is the main location for the business, it could be the trading address
    # or the registered address or a completely different address
    address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    address_country = models.ForeignKey(
        metadata_models.Country,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='companies_with_country_address',
    )
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

    registered_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_country = models.ForeignKey(
        metadata_models.Country,
        related_name='companies_with_country_registered_address',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

    headquarter_type = models.ForeignKey(
        metadata_models.HeadquarterType, blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    one_list_tier = models.ForeignKey(
        OneListTier,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
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
    pending_dnb_investigation = models.BooleanField(
        default=False,
        help_text='Whether this company is to be investigated by DNB.',
    )
    dnb_investigation_data = JSONField(
        null=True,
        blank=True,
    )
    export_potential = models.CharField(
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        choices=EXPORT_POTENTIAL_SCORES,
        help_text='Score that signifies export potential, imported from Data Science',
    )

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    class Meta:
        verbose_name_plural = 'companies'
        permissions = (
            (CompanyPermission.view_company_document.value, 'Can view company document'),
            (CompanyPermission.view_company_timeline.value, 'Can view company timeline'),
            (CompanyPermission.export_company.value, 'Can export company'),
            (
                CompanyPermission.change_regional_account_manager.value,
                'Can change regional account manager',
            ),
        )
        indexes = [
            # For datasets app which includes API endpoints to be consumed by data-flow
            models.Index(fields=('created_on', 'id')),
        ]

    @property
    def uk_based(self):
        """Whether a company is based in the UK or not."""
        if not self.address_country:
            return None

        united_kingdom_id = uuid.UUID(constants.Country.united_kingdom.value.id)
        return self.address_country.id == united_kingdom_id

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

    def get_active_future_export_countries(self):
        """
        Get a list of unique countries for which there are active (non-deleted)
        CompanyExportCountry Objects
        """
        if (
            hasattr(self, '_prefetched_objects_cache')
            and 'unfiltered_export_countries' in self._prefetched_objects_cache
        ):
            # If unfiltered_export_countries has been prefetched, we assume
            # that unfiltered_export_countries__country has been as well.
            # If it hasn't then the below will cause N queries to get each country.
            return sorted([
                cec.country
                for cec
                in self.unfiltered_export_countries.all()
                if not cec.disabled
            ], key=lambda c: c.id)
        else:
            # An optimised query to get the countries in the case where
            # the necessary prefetches have not been made.
            return list(metadata_models.Country.objects.filter(
                id__in=self.unfiltered_export_countries.filter(
                    disabled_on=None,
                ).values_list('country_id'),
            ).order_by('id'))

    def mark_as_transferred(self, to, reason, user):
        """
        Marks a company record as having been transferred to another company record.

        This is used, for example, for marking a company as a duplicate record.
        """
        self.modified_by = user
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

    def get_group_global_headquarters(self):
        """
        :returns: the Global Headquarters for the group that this company is part of.
        """
        if self.global_headquarters:
            return self.global_headquarters
        return self

    def get_one_list_group_tier(self):
        """
        :returns: the One List Tier of the group this company is part of.
        """
        return self.get_group_global_headquarters().one_list_tier

    def get_one_list_group_core_team(self):
        """
        :returns: the One List Core Team for the group that this company is part of
            as a list of dicts with `adviser` and `is_global_account_manager`.
        """
        group_global_headquarters = self.get_group_global_headquarters()
        global_account_manager = group_global_headquarters.one_list_account_owner

        core_team = []
        # add global account manager first
        if global_account_manager:
            core_team.append(
                {
                    'adviser': global_account_manager,
                    'is_global_account_manager': True,
                },
            )

        # add all other core members excluding the global account manager
        # who might have already been added
        team_members = group_global_headquarters.one_list_core_team_members.exclude(
            adviser=global_account_manager,
        ).select_related(
            'adviser',
            'adviser__dit_team',
            'adviser__dit_team__uk_region',
            'adviser__dit_team__country',
        ).order_by(
            'adviser__first_name',
            'adviser__last_name',
        )

        core_team.extend(
            {
                'adviser': team_member.adviser,
                'is_global_account_manager': False,
            }
            for team_member in team_members
        )
        return core_team

    def get_one_list_group_global_account_manager(self):
        """
        :returns: the One List Global Account Manager for the group that this
            company is part of.
        """
        group_global_headquarters = self.get_group_global_headquarters()
        return group_global_headquarters.one_list_account_owner


class OneListCoreTeamMember(models.Model):
    """
    Adviser who is a member of the One List Core Team of a company.

    When a company is account managed and added to the One List,
    a Core Team is established.
    This usually includes:
    - one and only one global account manager
    - a local account manager from the country where the company is based
    - one or more local account managers from the country where the company
        is exporting to or investing in

    However, this layout is not always as strict.
    Other roles might exist and a single person can also have multiple roles.

    This team is called "Core Team" because it's official and does not change
    often. Usually, a wider team around a company is established as well.
    This team includes specialists and other advisers needed for short-term
    and more reactive support.

    Company.one_list_account_owner who represents the global account manager
    is kept on the company record for now even though it's in theory part of
    the Core Team.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='one_list_core_team_members',
    )
    adviser = models.ForeignKey(
        'company.Advisor',
        on_delete=models.CASCADE,
        related_name='one_list_core_team_memberships',
    )

    def __str__(self):
        """Human-readable representation."""
        return f'{self.adviser} - One List Core Team member of {self.company}'

    class Meta:
        unique_together = (
            ('company', 'adviser'),
        )


class CompaniesHouseCompany(models.Model):
    """Representation of Companies House company."""

    name = models.CharField(max_length=MAX_LENGTH)
    company_number = models.CharField(max_length=MAX_LENGTH, unique=True)
    company_category = models.CharField(max_length=MAX_LENGTH, blank=True)
    company_status = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_3 = models.CharField(max_length=MAX_LENGTH, blank=True)
    sic_code_4 = models.CharField(max_length=MAX_LENGTH, blank=True)
    uri = models.CharField(max_length=MAX_LENGTH, blank=True)
    incorporation_date = models.DateField(null=True)

    registered_address_1 = models.CharField(max_length=MAX_LENGTH)
    registered_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_town = models.CharField(max_length=MAX_LENGTH)
    registered_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    registered_address_country = models.ForeignKey(
        metadata_models.Country,
        related_name='companieshousecompanies_with_country_registered_address',
        on_delete=models.PROTECT,
    )
    registered_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

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


@reversion.register_base_model()
class CompanyExportCountry(BaseModel, DisableableModel):
    """
    Record that a Company is interested in exporting to a Country.
    Source can be either 'user', indicating that the country was entered manually
    by a user on the frontend,
    or 'external', indicating that the country came in via an import from data science.
    Data science imports should not be able to remove any user-entered countries,
    only add to them.
    On the other hand, the user should be able to override and delete countries that
    came from data science. When this happens, the 'deleted' field is set to True.
    """

    SOURCES = Choices(
        ('user', 'User entered'),
        ('external', 'External'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    country = models.ForeignKey(
        metadata_models.Country,
        on_delete=models.CASCADE,
        related_name='companies_with_interest',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='unfiltered_export_countries',
    )
    sources = ArrayField(
        models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH, choices=SOURCES),
    )
    disabled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    @property
    def disabled(self):
        """
        Return boolean indicating whether country is disabled.
        """
        return bool(self.disabled_on)

    def disable(self, user=None):
        """
        Disable by setting disabled_on to current time and disabled_by to `user`.
        `user` should be None if this is not the result of user action.
        """
        self._dirty = True
        self.disabled_on = now()
        self.disabled_by = user

    def enable(self, user=None):
        """
        Enable by setting disabled_on and disabled_by to None,
        and setting modified_by to `user`.
        """
        self._dirty = True
        self.disabled_on = None
        self.disabled_by = None
        self.modified_by = user

    def add_source(self, source, source_time, user=None):
        """
        Add a source to the sources list.
        Conditionally re-enable if disabled.
        """
        if source == CompanyExportCountry.SOURCES.user and user is None:
            raise ValueError(
                f'user argument is required if source is {CompanyExportCountry.SOURCES.user}',
            )
        if source not in self.sources:
            self.sources.append(source)
            self._dirty = True
        if self.disabled:
            if (
                source == CompanyExportCountry.SOURCES.user
                or not self.disabled_by
                or source_time > self.disabled_on
            ):
                self.enable(user)

    def remove_source(self, source, user=None):
        """
        Remove a source from the sources list.
        Conditionally disable if enabled.
        """
        if source == CompanyExportCountry.SOURCES.user and user is None:
            raise ValueError(
                f'user argument is required if source is {CompanyExportCountry.SOURCES.user}',
            )
        if source in self.sources:
            self.sources.remove(source)
            self._dirty = True
        if (
            not self.disabled
            and (
                self.sources == []
                or source == CompanyExportCountry.SOURCES.user
            )
        ):
            # User source removal should always disable.
            # Other sources should only disable if there are no other sources left.
            self.disable(user)

    def save_if_dirty(self):
        """
        If the attribute _dirty is set and truthy,
        save the instance and then remove the _dirty attr.
        """
        if getattr(self, '_dirty', False):
            super().save()
            del self._dirty

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['country', 'company'],
                name='unique_country_company',
            ),
        ]
        verbose_name_plural = 'company export countries'

    def __str__(self):
        """
        Human readable name
        """
        return (
            f'{self.company} interested in {self.country}; '
            f'Sources: {self.sources}; Disabled: {self.disabled}'
        )
