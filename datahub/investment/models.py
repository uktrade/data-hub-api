"""Investment project models."""

import uuid
from collections import namedtuple
from itertools import chain

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from model_utils import Choices
from mptt.fields import TreeForeignKey

from datahub.core import reversion
from datahub.core.constants import InvestmentProjectStage
from datahub.core.models import (
    ArchivableModel,
    BaseConstantModel,
    BaseModel,
)
from datahub.core.utils import StrEnum

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
    add = 'add_investmentproject'
    delete = 'delete_investmentproject'
    export = 'export_investmentproject'
    view_investmentproject_document = 'view_investmentproject_document'


class IProjectAbstract(models.Model):
    """The core part of an investment project."""

    class Meta:
        abstract = True

    PRIORITIES = Choices(
        ('1_low', 'low', 'Low'),
        ('2_medium', 'medium', 'Medium'),
        ('3_high', 'high', 'High'),
    )

    STATUSES = Choices(
        ('ongoing', 'Ongoing'),
        ('delayed', 'Delayed'),
        ('dormant', 'Dormant'),
        ('lost', 'Lost'),
        ('abandoned', 'Abandoned'),
        ('won', 'Won'),
    )

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
    quotable_as_public_case_study = models.NullBooleanField()
    actual_land_date = models.DateField(blank=True, null=True)
    likelihood_of_landing = models.IntegerField(blank=True, null=True)
    priority = models.CharField(max_length=MAX_LENGTH, choices=PRIORITIES, blank=True, null=True)

    approved_commitment_to_invest = models.NullBooleanField()
    approved_fdi = models.NullBooleanField()
    approved_good_value = models.NullBooleanField()
    approved_high_value = models.NullBooleanField()
    approved_landed = models.NullBooleanField()
    approved_non_fdi = models.NullBooleanField()

    stage = models.ForeignKey(
        'metadata.InvestmentProjectStage', on_delete=models.PROTECT,
        related_name='investment_projects',
        default=InvestmentProjectStage.prospect.value.id,
    )
    status = models.CharField(
        max_length=MAX_LENGTH, choices=STATUSES, default=STATUSES.ongoing,
    )
    reason_delayed = models.TextField(blank=True, null=True)
    reason_abandoned = models.TextField(blank=True, null=True)
    date_abandoned = models.DateField(blank=True, null=True)
    reason_lost = models.TextField(blank=True, null=True)
    date_lost = models.DateField(blank=True, null=True)
    country_lost_to = models.ForeignKey(
        'metadata.Country', related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
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
            return self.investor_company.registered_address_country
        return None

    @property
    def client_relationship_manager_team(self):
        """The DIT team associated with the client relationship manager."""
        if self.client_relationship_manager:
            return self.client_relationship_manager.dit_team
        return None


class IProjectValueAbstract(models.Model):
    """The value part of an investment project."""

    class Meta:
        abstract = True

    fdi_value = models.ForeignKey(
        'metadata.FDIValue', related_name='investment_projects', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    client_cannot_provide_total_investment = models.NullBooleanField()
    total_investment = models.DecimalField(
        null=True, max_digits=19,
        decimal_places=0, blank=True,
    )
    client_cannot_provide_foreign_investment = models.NullBooleanField()
    foreign_equity_investment = models.DecimalField(
        null=True, max_digits=19, decimal_places=0, blank=True,
    )
    government_assistance = models.NullBooleanField()
    some_new_jobs = models.NullBooleanField()
    number_new_jobs = models.IntegerField(null=True, blank=True)
    will_new_jobs_last_two_years = models.NullBooleanField()
    average_salary = models.ForeignKey(
        'metadata.SalaryRange', related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    number_safeguarded_jobs = models.IntegerField(null=True, blank=True)
    r_and_d_budget = models.NullBooleanField()
    non_fdi_r_and_d_budget = models.NullBooleanField(
        verbose_name='has associated non-FDI R&D project',
    )
    associated_non_fdi_r_and_d_project = models.ForeignKey(
        'InvestmentProject', related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='associated non-FDI R&D project',
    )
    new_tech_to_uk = models.NullBooleanField()
    export_revenue = models.NullBooleanField()


class IProjectRequirementsAbstract(models.Model):
    """The requirements part of an investment project."""

    class Meta:
        abstract = True

    client_requirements = models.TextField(blank=True, null=True)
    site_decided = models.NullBooleanField()
    address_1 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_2 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_town = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_postcode = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    client_considering_other_countries = models.NullBooleanField()

    uk_company_decided = models.NullBooleanField()
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
    project_assurance_adviser = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True, on_delete=models.SET_NULL,
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

    def save(self, *args, **kwargs):
        """Updates the stage log after saving."""
        adding = self._state.adding
        if (
            self.__project_manager_id is None
            and self.project_manager_id
            and self.project_manager_first_assigned_on is None
        ):
            self.project_manager_first_assigned_on = now()

        super().save(*args, **kwargs)

        self._update_stage_log(adding)
        self.__project_manager_id = self.project_manager_id

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
        )
        default_permissions = (
            'add',
            'change_all',
            'delete',
            'view_all',
        )

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


class InvestmentProjectCode(models.Model):
    """An investment project number used for project codes.

    These are generated for new projects (but not for projects migrated from CDMS).

    This is required because Django does not allow AutoFields that are not primary keys,
    and we use UUIDs for primary keys. This model has a standard auto-incrementing integer
    (serial) as a primary key.
    """

    project = models.OneToOneField(InvestmentProject, on_delete=models.CASCADE)


class SpecificProgramme(BaseConstantModel):
    """Specific Investment Programmes."""


class InvestorType(BaseConstantModel):
    """Investor Types."""


class Involvement(BaseConstantModel):
    """Level of Involvements."""


class InvestmentDeliveryPartner(BaseConstantModel):
    """Investment delivery partners."""
