"""Investment project models."""

import uuid
from collections import namedtuple
from itertools import chain

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from model_utils import Choices

from datahub.core.constants import InvestmentProjectStage
from datahub.core.models import (
    ArchivableModel,
    BaseConstantModel,
    BaseModel,
)
from datahub.core.utils import StrEnum
from datahub.documents.models import Document

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class InvestmentProjectPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can read or change all investment projects:

    read_all_investmentproject
    change_all_investmentproject


    The following codenames mean that the user can only read or change investment projects that
    they are associated with:

    read_associated_investmentproject
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

    read_all = 'read_all_investmentproject'
    read_associated = 'read_associated_investmentproject'
    change_all = 'change_all_investmentproject'
    change_associated = 'change_associated_investmentproject'
    add = 'add_investmentproject'
    delete = 'delete_investmentproject'
    read_investmentproject_document = 'read_investmentproject_document'


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
                  'data for estimated land date does not exist.'
    )
    estimated_land_date = models.DateField(null=True)
    investment_type = models.ForeignKey(
        'metadata.InvestmentType', on_delete=models.PROTECT,
        related_name='investment_projects'
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
        default=InvestmentProjectStage.prospect.value.id
    )
    status = models.CharField(
        max_length=MAX_LENGTH, choices=STATUSES, default=STATUSES.ongoing
    )
    reason_delayed = models.TextField(blank=True, null=True)
    reason_abandoned = models.TextField(blank=True, null=True)
    date_abandoned = models.DateField(blank=True, null=True)
    reason_lost = models.TextField(blank=True, null=True)
    date_lost = models.DateField(blank=True, null=True)
    country_lost_to = models.ForeignKey(
        'metadata.Country', related_name='+', null=True, blank=True, on_delete=models.SET_NULL
    )

    investor_company = models.ForeignKey(
        'company.Company', related_name='investor_investment_projects',
        null=True, blank=True, on_delete=models.CASCADE
    )
    investor_type = models.ForeignKey(
        'investment.InvestorType', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    intermediate_company = models.ForeignKey(
        'company.Company', related_name='intermediate_investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    level_of_involvement = models.ForeignKey(
        'investment.Involvement', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    specific_programme = models.ForeignKey(
        'investment.SpecificProgramme', related_name='+',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    client_contacts = models.ManyToManyField(
        'company.Contact', related_name='investment_projects', blank=True
    )
    client_relationship_manager = models.ForeignKey(
        'company.Advisor', related_name='investment_projects', null=True,
        blank=True, on_delete=models.SET_NULL
    )
    referral_source_adviser = models.ForeignKey(
        'company.Advisor', related_name='referred_investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    referral_source_activity = models.ForeignKey(
        'metadata.ReferralSourceActivity', related_name='investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    referral_source_activity_website = models.ForeignKey(
        'metadata.ReferralSourceWebsite', related_name='investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    referral_source_activity_marketing = models.ForeignKey(
        'metadata.ReferralSourceMarketing', related_name='investment_projects',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    referral_source_activity_event = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    fdi_type = models.ForeignKey(
        'metadata.FDIType', related_name='investment_projects', null=True,
        blank=True, on_delete=models.SET_NULL
    )
    sector = models.ForeignKey(
        'metadata.Sector', related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    business_activities = models.ManyToManyField(
        'metadata.InvestmentBusinessActivity',
        related_name='+',
        blank=True
    )
    other_business_activity = models.CharField(
        max_length=MAX_LENGTH, null=True, blank=True
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
        on_delete=models.SET_NULL
    )
    client_cannot_provide_total_investment = models.NullBooleanField()
    total_investment = models.DecimalField(null=True, max_digits=19,
                                           decimal_places=0, blank=True)
    client_cannot_provide_foreign_investment = models.NullBooleanField()
    foreign_equity_investment = models.DecimalField(
        null=True, max_digits=19, decimal_places=0, blank=True
    )
    government_assistance = models.NullBooleanField()
    some_new_jobs = models.NullBooleanField()
    number_new_jobs = models.IntegerField(null=True, blank=True)
    will_new_jobs_last_two_years = models.NullBooleanField()
    average_salary = models.ForeignKey(
        'metadata.SalaryRange', related_name='+', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    number_safeguarded_jobs = models.IntegerField(null=True, blank=True)
    r_and_d_budget = models.NullBooleanField()
    non_fdi_r_and_d_budget = models.NullBooleanField(
        verbose_name='has associated non-FDI R&D project'
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
        null=True, blank=True, on_delete=models.SET_NULL
    )
    competitor_countries = models.ManyToManyField('metadata.Country', related_name='+', blank=True)
    uk_region_locations = models.ManyToManyField(
        'metadata.UKRegion', related_name='+', blank=True,
        verbose_name='possible UK regions',
    )
    actual_uk_regions = models.ManyToManyField(
        'metadata.UKRegion', related_name='+', blank=True,
        verbose_name='actual UK regions',
    )
    strategic_drivers = models.ManyToManyField(
        'metadata.InvestmentStrategicDriver',
        related_name='investment_projects', blank=True
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this '
                  'investment project.'
    )


class IProjectTeamAbstract(models.Model):
    """The team part of an investment project."""

    class Meta:
        abstract = True

    project_manager = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True, on_delete=models.SET_NULL
    )
    project_assurance_adviser = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True, on_delete=models.SET_NULL
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


_AssociatedToManyField = namedtuple(
    '_AssociatedToManyField', ('field_name', 'subfield_name', 'es_field_name')
)


class InvestmentProject(ArchivableModel, IProjectAbstract,
                        IProjectValueAbstract, IProjectRequirementsAbstract,
                        IProjectTeamAbstract, BaseModel):
    """An investment project."""

    _ASSOCIATED_ADVISER_TO_ONE_FIELDS = (
        'created_by',
        'client_relationship_manager',
        'project_manager',
        'project_assurance_adviser',
    )

    _ASSOCIATED_ADVISER_TO_MANY_FIELDS = (
        _AssociatedToManyField(
            field_name='team_members', subfield_name='adviser', es_field_name='team_members'
        ),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    def __str__(self):
        """Human-readable name for admin section etc."""
        company_name = self.investor_company or 'No company'
        return f'{company_name} – {self.name}'

    class Meta:
        permissions = (
            (
                InvestmentProjectPermission.read_all.value,
                'Can read all investment project'
            ),
            (
                InvestmentProjectPermission.read_associated.value,
                'Can read associated investment project'
            ),
            (
                InvestmentProjectPermission.change_associated.value,
                'Can change associated investment project'
            ),
            (
                InvestmentProjectPermission.read_investmentproject_document.value,
                'Can read investment project document'
            ),
        )
        default_permissions = (
            'add',
            'change_all',
            'delete',
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


class InvestmentProjectTeamMember(models.Model):
    """Intermediary M2M model for investment project team members.

    ManyToManyField with through is not used in the InvestmentProject model, because
    it makes working with DRF serialisers difficult (as it would return advisers rather than
    instances of this model).

    No default permissions are defined on this model as permissions from the InvestmentProject
    model are used and enforced instead. This is to avoid unnecessary complexity in the
    permissions model, where permissions on both models would need to be checked. (A custom read
    permission is also not defined for the same reason, but also because team members are
    returned in investment project responses in the investment and search APIs.)
    """

    investment_project = models.ForeignKey(
        InvestmentProject, on_delete=models.CASCADE, related_name='team_members'
    )
    adviser = models.ForeignKey('company.Advisor', on_delete=models.CASCADE, related_name='+')
    role = models.CharField(max_length=MAX_LENGTH)

    def __str__(self):
        """Human-readable representation."""
        return f'{self.investment_project} – {self.adviser} – {self.role}'

    class Meta:
        unique_together = (('investment_project', 'adviser'),)
        default_permissions = ()


class InvestmentProjectCode(models.Model):
    """An investment project number used for project codes.

    These are generated for new projects (but not for projects migrated from CDMS).

    This is required because Django does not allow AutoFields that are not primary keys,
    and we use UUIDs for primary keys. This model has a standard auto-incrementing integer
    (serial) as a primary key.
    """

    project = models.OneToOneField(InvestmentProject, on_delete=models.CASCADE)


class IProjectDocument(BaseModel, ArchivableModel):
    """Investment Project Document."""

    BUCKET_PREFIX = 'investment-documents'
    DOC_TYPES = Choices(
        ('actual_land_date', 'Actual land date'),
        ('hq', 'Global/European HQ evidence'),
        ('foreign_ownership', 'Foreign ownership evidence'),
        ('operations_commenced', 'Operations commenced'),
        ('total_investment', 'Total investment'),
        ('foreign_equity_investment', 'Foreign equity investment'),
        ('number_new_jobs', 'Number new jobs'),
        ('number_safeguarded_jobs', 'Number safeguarded jobs'),
        ('r_and_d_budget', 'R and D budget'),
        ('new_tech_to_uk', 'New tech to uk'),
        ('export_revenue', 'Export revenue'),
        ('average_salary', 'Average salary'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        InvestmentProject,
        related_name='documents',
        on_delete=models.CASCADE,
    )
    doc_type = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH, choices=DOC_TYPES)
    filename = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    document = models.OneToOneField(Document, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'investment project document'
        verbose_name_plural = 'investment project documents'
        unique_together = (
            ('project', 'doc_type', 'filename'),
        )
        permissions = (('read_iprojectdocument', 'Can read investment project document'),)

    @property
    def signed_url(self):
        """Generate pre-signed download URL."""
        return self.document.generate_signed_url()

    @property
    def signed_upload_url(self):
        """Generate pre-signed upload URL."""
        return self.document.generate_signed_upload_url()

    def delete(self, using=None, keep_parents=False):
        """Ensure document is removed when parent is being deleted."""
        result = super().delete(using, keep_parents)
        self.document.delete(using, keep_parents)
        return result

    @classmethod
    def create_from_declaration_request(cls, project, field, filename):
        """Create investment document along with correct Document creation."""
        with transaction.atomic():
            doc = Document(
                path=f'{cls.BUCKET_PREFIX}/{project.id}/{field}/{filename}',
            )
            doc.save()
            investment_doc = cls(
                project=project,
                doc_type=field,
                filename=filename,
                document=doc,
            )
            investment_doc.save()

        return investment_doc


class SpecificProgramme(BaseConstantModel):
    """Specific Investment Programmes."""


class InvestorType(BaseConstantModel):
    """Investor Types."""


class Involvement(BaseConstantModel):
    """Level of Involvements."""
