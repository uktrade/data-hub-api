"""Investment project models."""

import uuid
from collections import namedtuple
from itertools import chain

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from mptt.fields import TreeForeignKey
from reversion.models import Revision


from datahub.core import reversion
from datahub.core.constants import InvestmentProjectStage
from datahub.core.models import (
    ArchivableModel,
    BaseConstantModel,
    BaseModel,
    BaseOrderedConstantModel,
)
from datahub.core.utils import force_uuid, get_front_end_url, StrEnum
from datahub.investment.project import constants

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class InvestmentProjectPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can view or change all investment projects:

    view_all_investmentproject
    change_all_investmentproject

    User needs following permission to change investment project stage to Won:

    change_stage_to_won_investment_project

    Users with the following permission can change the stage of a project to any of the five
    stages, either forwards or backwards. This permission will bypass the existing field validated
    checks, meaning a project can be moved to a stage without the related fields being filled in.

    change_to_any_stage_investmentproject

    The following codenames mean that the user can only view or change investment projects that
    they are associated with:

    view_associated_investmentproject
    change_associated_investmentproject

    An associated project means one that was created by an adviser in the same team,
    or an adviser in the same team has been linked to the project via one of the attributes in
    InvestmentProject._ASSOCIATED_ADVISER_TO_ONE_FIELDS or
    InvestmentProject._ASSOCIATED_ADVISER_TO_MANY_FIELDS.


    Note that if both *_all_* and *_associated_* permissions are assigned to the  same user,
    the *_all_* permission will be the effective one.

    add_investmentproject and delete_investmentproject take on their normal meanings i.e. a
    project can be added, and any project can be deleted.
    """

    view_all = 'view_all_investmentproject'
    view_associated = 'view_associated_investmentproject'
    change_all = 'change_all_investmentproject'
    change_associated = 'change_associated_investmentproject'
    change_stage_to_won = 'change_stage_to_won_investmentproject'
    change_to_any_stage = 'change_to_any_stage_investmentproject'
    add = 'add_investmentproject'
    delete = 'delete_investmentproject'
    export = 'export_investmentproject'
    view_investmentproject_document = 'view_investmentproject_document'


class IProjectAbstract(models.Model):
    """The core part of an investment project."""

    class Meta:
        abstract = True

    class Priority(models.TextChoices):
        LOW = ('1_low', 'Low')
        MEDIUM = ('2_medium', 'Medium')
        HIGH = ('3_high', 'High')

    class Status(models.TextChoices):
        ONGOING = ('ongoing', 'Ongoing')
        DELAYED = ('delayed', 'Delayed')
        DORMANT = ('dormant', 'Dormant')
        LOST = ('lost', 'Lost')
        ABANDONED = ('abandoned', 'Abandoned')
        WON = ('won', 'Won')

    class Involvement(models.TextChoices):
        UNSPECIFIED = ('unspecified', 'Unspecified')
        NOT_INVOLVED = ('not_involved', 'Not involved')
        INVOLVED = ('involved', 'Involved')

    name = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField()
    comments = models.TextField(blank=True)
    anonymous_description = models.TextField(blank=True)
    allow_blank_estimated_land_date = models.BooleanField(
        default=False,
        help_text='Controls whether estimated land date is a required field. Intended for '
                  'projects migrated from CDMS in the verify win and won stages where legacy '
                  'data for estimated land date does not exist.',
    )
    estimated_land_date = models.DateField(null=True, blank=True)
    investment_type = models.ForeignKey(
        'metadata.InvestmentType', on_delete=models.PROTECT,
        related_name='investment_projects',
    )

    cdms_project_code = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    quotable_as_public_case_study = models.BooleanField(null=True)
    actual_land_date = models.DateField(
        blank=True,
        null=True,
    )
    likelihood_to_land = models.ForeignKey(
        'investment.LikelihoodToLand', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    priority = models.CharField(
        max_length=MAX_LENGTH,
        choices=Priority.choices,
        blank=True,
        null=True,
    )

    approved_commitment_to_invest = models.BooleanField(null=True)
    approved_fdi = models.BooleanField(null=True)
    approved_good_value = models.BooleanField(null=True)
    approved_high_value = models.BooleanField(null=True)
    approved_landed = models.BooleanField(null=True)
    approved_non_fdi = models.BooleanField(null=True)

    stage = models.ForeignKey(
        'metadata.InvestmentProjectStage', on_delete=models.PROTECT,
        related_name='investment_projects',
        default=InvestmentProjectStage.prospect.value.id,
    )
    status = models.CharField(
        max_length=MAX_LENGTH, choices=Status.choices, default=Status.ONGOING,
    )
    reason_delayed = models.TextField(blank=True, null=True)
    reason_abandoned = models.TextField(blank=True, null=True)
    date_abandoned = models.DateField(blank=True, null=True)
    reason_lost = models.TextField(blank=True, null=True)
    date_lost = models.DateField(blank=True, null=True)
    country_lost_to = models.ForeignKey(
        'metadata.Country', related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
    )
    country_investment_originates_from = models.ForeignKey(
        'metadata.Country', related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
        help_text='The country from which the investment originates',
    )

    investor_company = models.ForeignKey(
        'company.Company', related_name='investor_investment_projects',
        null=True, blank=True, on_delete=models.CASCADE,
    )
    investor_type = models.ForeignKey(
        'investment.InvestorType', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    intermediate_company = models.ForeignKey(
        'company.Company', related_name='intermediate_investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    level_of_involvement = models.ForeignKey(
        'investment.Involvement', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    specific_programme = models.ForeignKey(
        'investment.SpecificProgramme', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    client_contacts = models.ManyToManyField(
        'company.Contact', related_name='investment_projects', blank=True,
    )
    client_relationship_manager = models.ForeignKey(
        'company.Advisor', related_name='investment_projects', null=True,
        blank=True, on_delete=models.SET_NULL,
    )
    referral_source_adviser = models.ForeignKey(
        'company.Advisor', related_name='referred_investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    referral_source_activity = models.ForeignKey(
        'metadata.ReferralSourceActivity', related_name='investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    referral_source_activity_website = models.ForeignKey(
        'metadata.ReferralSourceWebsite', related_name='investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    referral_source_activity_marketing = models.ForeignKey(
        'metadata.ReferralSourceMarketing', related_name='investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    referral_source_activity_event = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    fdi_type = models.ForeignKey(
        'metadata.FDIType', related_name='investment_projects', null=True,
        blank=True, on_delete=models.SET_NULL,
    )
    sector = TreeForeignKey(
        'metadata.Sector', related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    business_activities = models.ManyToManyField(
        'metadata.InvestmentBusinessActivity',
        related_name='+',
        blank=True,
    )
    other_business_activity = models.CharField(
        max_length=MAX_LENGTH, null=True, blank=True,
    )

    @property
    def project_code(self):
        """A user-friendly project code.

        If a CDMS project code is held, that is returned. Otherwise a Data Hub project code
        beginning with DHP- is returned.
        """
        if self.cdms_project_code:
            return self.cdms_project_code
        try:
            project_num = self.investmentprojectcode.id
            return f'DHP-{project_num:08d}'
        except ObjectDoesNotExist:
            return None

    @property
    def investor_company_country(self):
        """The country of the investor company."""
        if self.investor_company:
            return self.investor_company.address_country
        return None

    @property
    def client_relationship_manager_team(self):
        """The DIT team associated with the client relationship manager."""
        if self.client_relationship_manager:
            return self.client_relationship_manager.dit_team
        return None

    @property
    def level_of_involvement_simplified(self):
        """Returns simplified level of involvement for the Investment Project."""
        if self.level_of_involvement_id is None:
            return self.Involvement.UNSPECIFIED

        not_involved_id = constants.Involvement.no_involvement.value.id
        if force_uuid(self.level_of_involvement_id) == force_uuid(not_involved_id):
            return self.Involvement.NOT_INVOLVED

        return self.Involvement.INVOLVED


class IProjectValueAbstract(models.Model):
    """The value part of an investment project."""

    class Meta:
        abstract = True

    fdi_value = models.ForeignKey(
        'metadata.FDIValue', related_name='investment_projects', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    client_cannot_provide_total_investment = models.BooleanField(null=True)
    total_investment = models.DecimalField(
        null=True, max_digits=19,
        decimal_places=0, blank=True,
    )
    client_cannot_provide_foreign_investment = models.BooleanField(null=True)
    foreign_equity_investment = models.DecimalField(
        null=True, max_digits=19, decimal_places=0, blank=True,
    )
    government_assistance = models.BooleanField(null=True)
    some_new_jobs = models.BooleanField(null=True)
    number_new_jobs = models.IntegerField(null=True, blank=True)
    will_new_jobs_last_two_years = models.BooleanField(null=True)
    average_salary = models.ForeignKey(
        'metadata.SalaryRange', related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    number_safeguarded_jobs = models.IntegerField(null=True, blank=True)
    r_and_d_budget = models.BooleanField(null=True)
    non_fdi_r_and_d_budget = models.BooleanField(
        null=True,
        verbose_name='has associated non-FDI R&D project',
    )
    associated_non_fdi_r_and_d_project = models.ForeignKey(
        'InvestmentProject', related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='associated non-FDI R&D project',
    )
    new_tech_to_uk = models.BooleanField(null=True)
    export_revenue = models.BooleanField(null=True)

    gva_multiplier = models.ForeignKey(
        'GVAMultiplier',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='investment_projects',
    )
    gross_value_added = models.DecimalField(
        max_digits=25,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=(
            'Denormalised GVA value which is automatically populated using '
            'the gva multiplier and the foreign equity investment value.'
        ),
    )


class IProjectRequirementsAbstract(models.Model):
    """The requirements part of an investment project."""

    class Meta:
        abstract = True

    client_requirements = models.TextField(blank=True, null=True)
    site_decided = models.BooleanField(null=True)
    address_1 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_2 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_town = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_postcode = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    client_considering_other_countries = models.BooleanField(null=True)

    uk_company_decided = models.BooleanField(null=True)
    uk_company = models.ForeignKey(
        'company.Company', related_name='investee_projects',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    competitor_countries = models.ManyToManyField('metadata.Country', related_name='+', blank=True)
    allow_blank_possible_uk_regions = models.BooleanField(
        default=False,
        help_text='Controls whether possible UK regions is a required field (after the prospect '
                  'stage). Intended for projects migrated from CDMS in the verify win and won '
                  'stages where legacy data for possible UK regions does not exist.',
    )
    uk_region_locations = models.ManyToManyField(
        'metadata.UKRegion', related_name='+', blank=True,
        verbose_name='possible UK regions',
    )
    actual_uk_regions = models.ManyToManyField(
        'metadata.UKRegion', related_name='+', blank=True,
        verbose_name='actual UK regions',
    )
    delivery_partners = models.ManyToManyField(
        'InvestmentDeliveryPartner', related_name='+', blank=True,
        verbose_name='investment delivery partners',
        help_text='These are the delivery partner(s) in the region(s) where the project landed.',
    )
    strategic_drivers = models.ManyToManyField(
        'metadata.InvestmentStrategicDriver',
        related_name='investment_projects', blank=True,
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this '
                  'investment project.',
    )


class IProjectTeamAbstract(models.Model):
    """The team part of an investment project."""

    class Meta:
        abstract = True

    project_manager = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True, on_delete=models.SET_NULL,
    )
    # field project_manager_first_assigned_on is being used for SPI reporting
    # it contains a datetime when first time a project manager has been assigned
    project_manager_first_assigned_on = models.DateTimeField(null=True, blank=True)
    # field project_manager_first_assigned_by is being used for SPI reporting
    # it contains a reference to an Adviser who first time assigned a project manager
    project_manager_first_assigned_by = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True, on_delete=models.SET_NULL,
    )
    project_manager_requested_on = models.DateTimeField(null=True, blank=True)

    project_assurance_adviser = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True, on_delete=models.SET_NULL,
    )
    project_manager_request_status = models.ForeignKey(
        'ProjectManagerRequestStatus', null=True, related_name='+', blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def project_manager_team(self):
        """The DIT team associated with the project manager."""
        if self.project_manager:
            return self.project_manager.dit_team
        return None

    @property
    def project_assurance_team(self):
        """The DIT team associated with the project assurance adviser."""
        if self.project_assurance_adviser:
            return self.project_assurance_adviser.dit_team
        return None


class IProjectSPIAbstract(models.Model):
    """The Service Performance Indicator (SPI) part of an investment project.

    It enables monitoring and measurement of the Investment Services Team’s (IST)
    key service performance indicators (SPIs).
    """

    class Meta:
        abstract = True

    project_arrived_in_triage_on = models.DateField(blank=True, null=True)
    proposal_deadline = models.DateField(blank=True, null=True)


_AssociatedToManyField = namedtuple(
    '_AssociatedToManyField', ('field_name', 'subfield_name', 'es_field_name'),
)


@reversion.register_base_model()
class InvestmentProject(
    ArchivableModel,
    IProjectAbstract,
    IProjectValueAbstract,
    IProjectRequirementsAbstract,
    IProjectTeamAbstract,
    IProjectSPIAbstract,
    BaseModel,
):
    """An investment project."""

    _ASSOCIATED_ADVISER_TO_ONE_FIELDS = (
        'created_by',
        'client_relationship_manager',
        'project_manager',
        'project_assurance_adviser',
    )

    _ASSOCIATED_ADVISER_TO_MANY_FIELDS = (
        _AssociatedToManyField(
            field_name='team_members', subfield_name='adviser', es_field_name='team_members',
        ),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    def __init__(self, *args, **kwargs):
        """Keep the original stage value so that we can see if it changes when saving."""
        super().__init__(*args, **kwargs)
        self.__stage_id = self.stage_id
        self.__project_manager_id = self.project_manager_id

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    def save(self, *args, **kwargs):
        """Updates the stage log after saving."""
        adding = self._state.adding
        super().save(*args, **kwargs)

        self._update_stage_log(adding)

    def _update_stage_log(self, adding):
        """Creates a log of changes to stage field.

        This allows us to construct the timeline of changes to the stage field as
        required for Service Performance Indicators (SPI).
        """
        stage_changed_on = None

        if adding:
            stage_changed_on = self.created_on
        else:
            if self.__stage_id != self.stage_id:
                stage_changed_on = self.modified_on

        if stage_changed_on:
            InvestmentProjectStageLog.objects.create(
                investment_project_id=self.pk,
                stage_id=self.stage_id,
                created_on=stage_changed_on,
            )

    def __str__(self):
        """Human-readable name for admin section etc."""
        company_name = self.investor_company or 'No company'
        return f'{company_name} – {self.name}'

    class Meta:
        permissions = (
            (
                InvestmentProjectPermission.view_associated.value,
                'Can view associated investment project',
            ),
            (
                InvestmentProjectPermission.change_associated.value,
                'Can change associated investment project',
            ),
            (
                InvestmentProjectPermission.export.value,
                'Can export investment project',
            ),
            (
                InvestmentProjectPermission.view_investmentproject_document.value,
                'Can view investment project document',
            ),
            (
                InvestmentProjectPermission.change_stage_to_won.value,
                'Can change investment project stage to won',
            ),
            (
                InvestmentProjectPermission.change_to_any_stage.value,
                'Can change investment project to any stage',
            ),
        )
        default_permissions = (
            'add',
            'change_all',
            'delete',
            'view_all',
        )
        indexes = [
            # For activity stream
            models.Index(fields=('created_on', 'id')),
        ]

    def get_associated_advisers(self):
        """Get the advisers associated with the project."""
        return chain(
            self._get_associated_to_one_advisers(),
            self._get_associated_to_many_advisers(),
        )

    @classmethod
    def get_association_fields(cls):
        """
        Gets a list of to-one association fields, and to-many association fields.

        These are used (as part of permissions) to determine if an adviser's team is associated
        with a project.
        """
        return cls._ASSOCIATED_ADVISER_TO_ONE_FIELDS, cls._ASSOCIATED_ADVISER_TO_MANY_FIELDS

    def _get_associated_to_one_advisers(self):
        advisers = (getattr(self, field) for field in self._ASSOCIATED_ADVISER_TO_ONE_FIELDS)
        return filter(None, advisers)

    def _get_associated_to_many_advisers(self):
        for field in self._ASSOCIATED_ADVISER_TO_MANY_FIELDS:
            field_instance = getattr(self, field.field_name)
            for item in field_instance.all():
                adviser = getattr(item, field.subfield_name)
                if adviser:
                    yield adviser


@reversion.register_base_model()
class InvestmentProjectTeamMember(models.Model):
    """Intermediary M2M model for investment project team members.

    ManyToManyField with through is not used in the InvestmentProject model, because
    it makes working with DRF serialisers difficult (as it would return advisers rather than
    instances of this model).

    No default permissions are defined on this model as permissions from the InvestmentProject
    model are used and enforced instead. This is to avoid unnecessary complexity in the
    permissions model, where permissions on both models would need to be checked. (A view
    permission is also omitted because team members are returned in investment project responses
    in the investment and search APIs.)
    """

    investment_project = models.ForeignKey(
        InvestmentProject, on_delete=models.CASCADE, related_name='team_members',
    )
    adviser = models.ForeignKey('company.Advisor', on_delete=models.CASCADE, related_name='+')
    role = models.CharField(max_length=MAX_LENGTH)

    def __str__(self):
        """Human-readable representation."""
        return f'{self.investment_project} – {self.adviser} – {self.role}'

    class Meta:
        unique_together = (('investment_project', 'adviser'),)
        default_permissions = ()


class InvestmentProjectStageLog(models.Model):
    """Investment Project stage log.

    It is being used to support reporting of Service Performance Indicators (SPIs).
    """

    investment_project = models.ForeignKey(
        InvestmentProject, on_delete=models.CASCADE, related_name='stage_log',
    )
    stage = models.ForeignKey(
        'metadata.InvestmentProjectStage', on_delete=models.PROTECT,
        related_name='+',
    )
    created_on = models.DateTimeField()

    class Meta:
        ordering = ('created_on',)

    def __str__(self):
        """Human-readable representation."""
        return f'{self.investment_project} – {self.created_on} – {self.stage}'


@reversion.register_base_model()
class InvestmentActivity(BaseModel):
    """An investment activity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.OneToOneField(Revision, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    activity_type = models.ForeignKey(
        'investment.InvestmentActivityType',
        on_delete=models.PROTECT,
        related_name='+',
    )
    investment_project = models.ForeignKey(
        InvestmentProject,
        on_delete=models.CASCADE,
        related_name='activities',
    )

    class Meta:
        ordering = ('-created_on',)

    def __str__(self):
        """Human-readable representation"""
        return self.text


class InvestmentProjectCode(models.Model):
    """An investment project number used for project codes.

    These are generated for new projects (but not for projects migrated from CDMS).

    This is required because Django does not allow AutoFields that are not primary keys,
    and we use UUIDs for primary keys. This model has a standard auto-incrementing integer
    (serial) as a primary key.
    """

    project = models.OneToOneField(InvestmentProject, on_delete=models.CASCADE)


class InvestmentSector(models.Model):
    """Investment Sector a link between a DIT Sector and an FDI SIC Grouping."""

    sector = models.OneToOneField(
        'metadata.Sector',
        primary_key=True,
        on_delete=models.PROTECT,
    )
    fdi_sic_grouping = models.ForeignKey(
        'investment.FDISICGrouping',
        related_name='investment_sectors',
        on_delete=models.PROTECT,
    )

    def __str__(self):
        """Human-readable representation"""
        return f'{self.sector} Sector - {self.fdi_sic_grouping}'


class FDISICGrouping(BaseConstantModel):
    """FDI Standard Industrial Classification Grouping used for GVA."""

    class Meta(BaseConstantModel.Meta):
        verbose_name = 'FDI SIC Grouping'


class GVAMultiplier(models.Model):
    """
    Gross Value Added Multiplier.

    To calculate the GVA of an investment project a constant (multiplier) is multiplied
    by the foreign equity investment value.

    The multiplier has been derived from historical investment project data and could change for
    each financial year when more data is analysed.

    The multiplier value is linked to an fdi sic grouping.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    fdi_sic_grouping = models.ForeignKey(
        'investment.FDISICGrouping',
        related_name='gva_multipliers',
        on_delete=models.CASCADE,
    )
    multiplier = models.DecimalField(
        max_digits=7,
        decimal_places=6,
    )
    financial_year = models.IntegerField(
        help_text='The year from which the gva multiplier should apply from.',
    )

    class Meta:
        verbose_name = 'GVA Multiplier'
        unique_together = (('fdi_sic_grouping', 'financial_year'),)

    def __str__(self):
        """Human-readable representation"""
        return f'GVA Multiplier for {self.fdi_sic_grouping} - {self.financial_year}'


class SpecificProgramme(BaseConstantModel):
    """Specific Investment Programmes."""


class InvestorType(BaseConstantModel):
    """Investor Types."""


class Involvement(BaseConstantModel):
    """Level of Involvements."""


class InvestmentDeliveryPartner(BaseConstantModel):
    """Investment delivery partners."""


class LikelihoodToLand(BaseOrderedConstantModel):
    """Likelihood to land."""


class ProjectManagerRequestStatus(BaseConstantModel):
    """Project manager request status."""


class InvestmentActivityType(BaseConstantModel):
    """Investment activity type."""
