import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from mptt.fields import TreeForeignKey

from datahub.company.models import (
    Advisor,
    Company,
    Contact,
    ExportExperience,
)
from datahub.core import reversion
from datahub.core.models import BaseModel, BaseOrderedConstantModel
from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.utils import calculate_totals_for_export_win
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)

from datahub.reminder.models import EmailDeliveryStatus


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BaseExportWinManager(models.Manager):
    """Base manager for common export win queries."""

    def all_wins(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)


class BaseExportWinSoftDeleteManager(BaseExportWinManager):
    """Manager for handling non-deleted export win queries."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_deleted=False)
        )

    def soft_deleted(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .filter(is_deleted=True)
        )


class AnonymousWinManager(BaseExportWinManager):
    """Manager for handling anonymous export win queries."""

    def anonymous_win(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .filter(is_anonymous_win=True, is_deleted=False)
        )


class BaseCustomerResponseSoftDeleteManager(models.Manager):
    """Base class for Customer response soft delete manager."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('win')
            .exclude(win__is_deleted=True)
        )

    def all_customer_responses(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)


class BaseExportWinOrderedConstantModel(BaseOrderedConstantModel):
    """Base class for an Export Win."""

    export_win_id = models.CharField(
        max_length=MAX_LENGTH,
    )

    class Meta:
        abstract = True
        ordering = ('order', )


class TeamType(BaseExportWinOrderedConstantModel):
    """Team type."""


class HQTeamRegionOrPost(BaseExportWinOrderedConstantModel):
    """HQ Team Region or Post."""

    team_type = models.ForeignKey(
        TeamType,
        related_name='hq_team_region_or_post',
        on_delete=models.CASCADE,
    )


class WinType(BaseExportWinOrderedConstantModel):
    """Win type."""


class BusinessPotential(BaseExportWinOrderedConstantModel):
    """Business potential."""


class SupportType(BaseExportWinOrderedConstantModel):
    """Support type."""


class ExpectedValueRelation(BaseExportWinOrderedConstantModel):
    """Expected value relation."""


class ExperienceCategories(BaseExportWinOrderedConstantModel):
    """Experience categories."""

    export_experience = models.ForeignKey(
        ExportExperience,
        related_name='export_wins_export_experience',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )


class BreakdownType(BaseExportWinOrderedConstantModel):
    """Breakdown type."""


class Rating(BaseExportWinOrderedConstantModel):
    """Rating."""


class Experience(BaseExportWinOrderedConstantModel):
    """Experience."""


class MarketingSource(BaseExportWinOrderedConstantModel):
    """Marketing source."""


class WithoutOurSupport(BaseExportWinOrderedConstantModel):
    """Without our support."""


class HVOProgrammes(BaseExportWinOrderedConstantModel):
    """HVO Programmes."""


class AssociatedProgramme(BaseExportWinOrderedConstantModel):
    """Associated Programme."""


class WinUKRegion(BaseExportWinOrderedConstantModel):
    """Export Win UK Region."""


class BaseLegacyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    legacy_id = models.IntegerField(blank=True, null=True, unique=True)

    class Meta:
        abstract = True

    @transaction.atomic
    def save(self, *args, **kwargs):
        # This means that the model isn't saved to the database yet and has no legacy_id set
        if self._state.adding and self.legacy_id is None:
            # Get the maximum legacy_id value from the database

            last_id = self.__class__.objects.all().aggregate(Max('legacy_id'))['legacy_id__max']

            # If there is a legacy_id, just use the last value and add 1 to it
            if last_id is not None and last_id >= EXPORT_WINS_LEGACY_ID_START_VALUE:
                self.legacy_id = last_id + 1
            else:
                self.legacy_id = EXPORT_WINS_LEGACY_ID_START_VALUE

        super().save(*args, **kwargs)


class HVC(BaseExportWinOrderedConstantModel, BaseLegacyModel):
    """HVC codes."""

    campaign_id = models.CharField(max_length=4)
    financial_year = models.PositiveIntegerField()

    class Meta:
        ordering = ('order', )
        unique_together = ('campaign_id', 'financial_year')

    def __str__(self):
        # note name includes code
        return f'{self.name} ({self.financial_year})'

    @property
    def campaign(self):
        """
        The name of the campaign alone without the code
        e.g. Africa Agritech or Italy Automotive
        """
        # names are always <Name of HVC: HVC code>
        return self.name.split(':')[0]

    @property
    def charcode(self):
        # see choices comment
        return f'{self.campaign_id}{self.financial_year}'

    @classmethod
    def get_by_charcode(cls, charcode):
        return cls.objects.get(campaign_id=charcode[:-2])


@reversion.register_base_model()
class Win(BaseModel):
    """Information about a given Export win, submitted by an officer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    adviser = models.ForeignKey(
        Advisor,
        related_name='wins',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    # Legacy field
    adviser_name = models.CharField(
        max_length=128,
        verbose_name='Adviser name',
        help_text='This is the name of the adviser who created the Win',
        blank=True,
    )
    # Legacy field
    adviser_email_address = models.EmailField(
        verbose_name='Adviser email address',
        blank=True,
    )
    company = models.ForeignKey(
        Company,
        related_name='wins',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # customers
    company_contacts = models.ManyToManyField(Contact, blank=True, related_name='wins')

    # legacy fields
    customer_name = models.CharField(max_length=128, verbose_name='Contact name')
    customer_job_title = models.CharField(max_length=128, verbose_name='Job title')
    customer_email_address = models.EmailField(verbose_name='Contact email')

    customer_location = models.ForeignKey(
        WinUKRegion,
        related_name='wins',
        verbose_name='HQ location',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    customer_location_data_hub = models.ForeignKey(
        UKRegion,
        related_name='wins',
        verbose_name='HQ location',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    business_type = models.CharField(
        max_length=128,
        verbose_name='What kind of business deal was this win?',
    )

    # Formerly a catch-all, since broken out into business_type,
    # name_of_customer, name_of_export and description.
    description = models.TextField(
        verbose_name='Summarise the support provided to help achieve this win',
    )
    name_of_customer = models.CharField(max_length=128, verbose_name='Overseas customer')
    name_of_customer_confidential = models.BooleanField(null=True)
    # type of business deal
    name_of_export = models.CharField(
        max_length=128,
        verbose_name='What are the goods or services?',
    )

    type = models.ForeignKey(
        WinType,
        related_name='wins',
        verbose_name='Type of win',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    date = models.DateField(verbose_name='Date business won [MM/YY]')
    country = models.ForeignKey(
        Country,
        related_name='wins',
        on_delete=models.PROTECT,
    )

    total_expected_export_value = models.BigIntegerField()
    goods_vs_services = models.ForeignKey(
        ExpectedValueRelation,
        related_name='wins',
        verbose_name='Does the expected value relate to',
        on_delete=models.PROTECT,
    )
    total_expected_non_export_value = models.BigIntegerField()
    total_expected_odi_value = models.BigIntegerField()

    sector = TreeForeignKey(
        Sector,
        related_name='wins',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_prosperity_fund_related = models.BooleanField(verbose_name='Prosperity Fund', default=False)
    # note, this consists of first 4 chars hvc code, final 2 chars the
    # financial year it applies to, see HVC.choices
    hvc = models.ForeignKey(
        HVC,
        related_name='wins',
        verbose_name='HVC code, if applicable',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    hvo_programme = models.ForeignKey(
        HVOProgrammes,
        related_name='wins',
        verbose_name='HVO Programme, if applicable',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    has_hvo_specialist_involvement = models.BooleanField(
        verbose_name='An HVO specialist was involved',
        default=False,
    )
    is_e_exported = models.BooleanField('E-exporting programme', default=False)

    type_of_support = models.ManyToManyField(SupportType)

    associated_programme = models.ManyToManyField(
        AssociatedProgramme,
        blank=True,
    )

    is_personally_confirmed = models.BooleanField(
        verbose_name='I confirm that this information is complete and accurate',
    )
    is_line_manager_confirmed = models.BooleanField(
        verbose_name='My line manager has confirmed the decision to record this win',
    )

    lead_officer = models.ForeignKey(
        Advisor,
        related_name='lead_officer_wins',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    team_members = models.ManyToManyField(
        Advisor,
        blank=True,
        related_name='team_export_wins',
    )

    # Legacy field
    lead_officer_name = models.CharField(
        max_length=128,
        verbose_name='Lead officer name',
        help_text='This is the name that will be included in the email to the customer',
    )
    # Legacy field
    lead_officer_email_address = models.EmailField(
        verbose_name='Lead officer email address',
        blank=True,
    )
    # Legacy field
    other_official_email_address = models.EmailField(
        verbose_name='Secondary email address',
        blank=True,
    )

    # Legacy field
    line_manager = models.ForeignKey(
        Advisor,
        related_name='line_manager_wins',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # Legacy field
    line_manager_name = models.CharField(
        max_length=128,
        verbose_name='Line manager',
    )

    team_type = models.ForeignKey(
        TeamType,
        related_name='wins',
        on_delete=models.PROTECT,
    )
    hq_team = models.ForeignKey(
        HQTeamRegionOrPost,
        related_name='wins',
        verbose_name='HQ team, Region or Post',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    business_potential = models.ForeignKey(
        BusinessPotential,
        related_name='wins',
        verbose_name='Medium-sized and high potential companies',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    export_experience = models.ForeignKey(
        ExportExperience,
        related_name='wins',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    export_wins_export_experience = models.ForeignKey(
        ExperienceCategories,
        related_name='wins',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    location = models.CharField(max_length=128, blank=True)

    complete = models.BooleanField(default=False)  # has an email been sent to the customer?
    audit = models.TextField(default='', blank=True)

    # Legacy data
    match_id = models.PositiveIntegerField(null=True, blank=True)
    company_name = models.CharField(
        max_length=128,
        verbose_name='Organisation or company name',
    )
    cdms_reference = models.CharField(
        max_length=128,
        verbose_name='Data Hub (Companies House) or CDMS reference number',
    )

    # Company export project ID, if Win has been converted from Export project
    company_export = models.ForeignKey(
        'company.CompanyExport',
        related_name='wins',
        verbose_name='Related company export project',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    is_deleted = models.BooleanField(default=False)
    migrated_on = models.DateTimeField(null=True, blank=True)
    is_anonymous_win = models.BooleanField(default=False)

    objects = BaseExportWinSoftDeleteManager()
    anonymous_objects = AnonymousWinManager()

    def __str__(self):
        if self.adviser:
            return (f'Export win {self.pk}: {self.adviser} <{self.adviser.email}> - '
                    f'{self.created_on.strftime("%Y-%m-%d %H:%M:%S") if self.created_on else ""}')
        else:
            return (
                f'Export win {self.pk} (legacy): {self.adviser_name} '
                f'<{self.adviser_email_address}> - '
                f'{self.created_on.strftime("%Y-%m-%d %H:%M:%S") if self.created_on else ""}'
            )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.total_expected_export_value = 0
            self.total_expected_non_export_value = 0
            self.total_expected_odi_value = 0
            super().save(*args, **kwargs)

        # Don't recalculate totals for migrated legacy Export wins
        if not self.migrated_on:
            calc_total = calculate_totals_for_export_win(self)
            self.total_expected_export_value = calc_total['total_export_value']
            self.total_expected_non_export_value = calc_total['total_non_export_value']
            self.total_expected_odi_value = calc_total['total_odi_value']
        super().save(*args, **kwargs)


class Breakdown(BaseModel, BaseLegacyModel):
    """Win breakdown."""

    win = models.ForeignKey(Win, related_name='breakdowns', on_delete=models.CASCADE)
    type = models.ForeignKey(
        BreakdownType,
        related_name='breakdowns',
        on_delete=models.PROTECT,
    )
    year = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    value = models.BigIntegerField()


class WinAdviser(BaseModel, BaseLegacyModel):
    """Win adviser."""

    adviser = models.ForeignKey(
        Advisor,
        related_name='win_advisers',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    win = models.ForeignKey(Win, related_name='advisers', on_delete=models.CASCADE)
    team_type = models.ForeignKey(
        TeamType,
        related_name='win_advisers',
        on_delete=models.PROTECT,
    )
    hq_team = models.ForeignKey(
        HQTeamRegionOrPost,
        related_name='win_advisers',
        verbose_name='HQ team, Region or Post',
        on_delete=models.PROTECT,
    )
    location = models.CharField(
        max_length=128,
        verbose_name='Location (if applicable)',
        blank=True,
    )
    # Legacy fields
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Adviser'

    def __str__(self):
        return f'Name: {self.adviser}, Team {self.team_type} - {self.hq_team}'


@reversion.register_base_model()
class CustomerResponse(BaseModel):
    """Customer response."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    win = models.OneToOneField(Win, related_name='customer_response', on_delete=models.CASCADE)
    responded_on = models.DateTimeField(null=True, blank=True)
    our_support = models.ForeignKey(
        Rating,
        related_name='our_support_customer_responses',
        verbose_name='Securing the win overall?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    access_to_contacts = models.ForeignKey(
        Rating,
        related_name='access_to_contacts_customer_responses',
        verbose_name='Gaining access to contacts?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    access_to_information = models.ForeignKey(
        Rating,
        related_name='access_to_information_customer_responses',
        verbose_name='Getting information or improved understanding of the country?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    improved_profile = models.ForeignKey(
        Rating,
        related_name='improved_profile_customer_responses',
        verbose_name='Improving your profile or credibility in the country?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    gained_confidence = models.ForeignKey(
        Rating,
        related_name='gained_confidence_customer_responses',
        verbose_name='Having confidence to explore or expand in the country?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    developed_relationships = models.ForeignKey(
        Rating,
        related_name='developed_relationships_customer_responses',
        verbose_name='Developing or nurturing critical relationships?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    overcame_problem = models.ForeignKey(
        Rating,
        related_name='overcame_problem_customer_responses',
        verbose_name=(
            'Overcoming a problem in the country (such as '
            'legal, regulatory, commercial)?'),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    involved_state_enterprise = models.BooleanField(
        verbose_name=(
            'The win involved a foreign government or state-owned enterprise (such as an '
            'intermediary or facilitator)'),
        default=False,
        null=True,
        blank=True,
    )
    interventions_were_prerequisite = models.BooleanField(
        verbose_name='Our support was a prerequisite to generate this export value',
        default=False,
        null=True,
        blank=True,
    )
    support_improved_speed = models.BooleanField(
        verbose_name='Our support helped you achieve this win more quickly',
        default=False,
        null=True,
        blank=True,
    )
    expected_portion_without_help = models.ForeignKey(
        WithoutOurSupport,
        related_name='customer_responses',
        verbose_name='What value do you estimate you would have achieved without our support?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    last_export = models.ForeignKey(
        Experience,
        related_name='customer_responses',
        verbose_name='Apart from this win, when did your company last export goods or services?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    has_enabled_expansion_into_new_market = models.BooleanField(
        verbose_name='It enabled you to expand into a new market',
        default=False,
        null=True,
        blank=True,
    )
    has_enabled_expansion_into_existing_market = models.BooleanField(
        verbose_name='It enabled you to maintain or expand in an existing market',
        default=False,
        null=True,
        blank=True,
    )
    has_increased_exports_as_percent_of_turnover = models.BooleanField(
        verbose_name='It enabled you to increase exports as a proportion of your turnover',
        default=False,
        null=True,
        blank=True,
    )
    company_was_at_risk_of_not_exporting = models.BooleanField(
        verbose_name="If you hadn't achieved this win, your company might have stopped exporting",
        default=False,
        null=True,
        blank=True,
    )
    has_explicit_export_plans = models.BooleanField(
        verbose_name=('Apart from this win, you already have specific plans to export in the next '
                      '12 months'),
        default=False,
        null=True,
        blank=True,
    )
    agree_with_win = models.BooleanField(
        null=True,
        verbose_name='Please confirm these details are correct',
        db_index=True,
    )
    case_study_willing = models.BooleanField(
        verbose_name=('Would you be willing for DBT/Exporting is GREAT to feature your success '
                      'in marketing materials?'),
        default=False,
        null=True,
        blank=True,
    )
    comments = models.TextField(
        blank=True,
        default='',
        verbose_name='Other comments or changes to the win details',
    )
    # name is a legacy field. Should only be used when importing legacy data.
    name = models.CharField(max_length=256, verbose_name='Your name')
    marketing_source = models.ForeignKey(
        MarketingSource,
        related_name='customer_responses',
        verbose_name='How did you first hear about DBT (or its predecessor, DIT)?',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    other_marketing_source = models.CharField(
        max_length=256,
        verbose_name='Other marketing source',
        default='',
        blank=True,
    )
    lead_officer_email_notification_id = models.UUIDField(null=True, blank=True)
    lead_officer_email_delivery_status = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        choices=EmailDeliveryStatus.choices,
        help_text='Email delivery status',
        default=EmailDeliveryStatus.UNKNOWN,
    )
    lead_officer_email_sent_on = models.DateTimeField(null=True, blank=True)

    objects = BaseCustomerResponseSoftDeleteManager()


class CustomerResponseToken(models.Model):
    """Customer Response Token"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    expires_on = models.DateTimeField()
    customer_response = models.ForeignKey(
        CustomerResponse, related_name='tokens', on_delete=models.CASCADE)
    email_notification_id = models.UUIDField(null=True, blank=True)
    email_delivery_status = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        choices=EmailDeliveryStatus.choices,
        help_text='Email delivery status',
        default=EmailDeliveryStatus.UNKNOWN)
    company_contact = models.ForeignKey(
        'company.Contact',
        related_name='tokens',
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    times_used = models.PositiveIntegerField(default=0)
    created_on = models.DateTimeField(db_index=True, null=True, blank=True, auto_now_add=True)
    adviser = models.ForeignKey(
        Advisor,
        related_name='admin_tokens',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    legacy_id = models.IntegerField(blank=True, null=True, unique=True)
    legacy_recipient = models.CharField(
        blank=True,
        max_length=256,
        verbose_name='Legacy recipient',
    )

    def __str__(self):
        return f'Token: {self.id} ({self.expires_on})'


@reversion.register_base_model()
class LegacyExportWinsToDataHubCompany(models.Model):
    """Maps Legacy Export win to Data Hub company."""

    id = models.UUIDField(primary_key=True)
    company = models.ForeignKey(
        Company,
        related_name='legacy_wins',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )


class LegacyExportWinsToDataHubAdminUser(models.Model):
    """Maps Legacy Export win admin user to Data Hub adviser."""

    email = models.CharField(max_length=MAX_LENGTH)
    adviser = models.ForeignKey(
        Advisor,
        related_name='legacy_admin_user',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )


class DeletedWin(Win):
    """Deleted win"""

    class Meta:
        proxy = True


@receiver(post_save, sender=Breakdown)
def update_total_values(sender, instance, **kwargs):
    """Save the right total values"""
    win = instance.win

    calc_total = calculate_totals_for_export_win(win)
    win.total_expected_export_value = calc_total['total_export_value']
    win.total_expected_non_export_value = calc_total['total_non_export_value']
    win.total_expected_odi_value = calc_total['total_odi_value']
    win.save()


class AnonymousWin(Win):
    """Anonymous win"""

    class Meta:
        proxy = True
