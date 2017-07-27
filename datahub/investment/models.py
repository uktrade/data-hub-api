"""Investment project models."""

import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from model_utils import Choices

from datahub.core.constants import InvestmentProjectStage
from datahub.core.models import ArchivableModel, BaseModel
from datahub.documents.models import Document

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class IProjectAbstract(models.Model):
    """The core part of an investment project."""

    class Meta:  # noqa: D101
        abstract = True

    PRIORITIES = Choices(
        ('1_low', 'low', 'Low'),
        ('2_medium', 'medium', 'Medium'),
        ('3_high', 'high', 'High'),
    )

    name = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField()
    nda_signed = models.BooleanField()
    estimated_land_date = models.DateField()
    investment_type = models.ForeignKey(
        'metadata.InvestmentType', on_delete=models.PROTECT,
        related_name='investment_projects'
    )

    cdms_project_code = models.CharField(max_length=MAX_LENGTH, blank=True,
                                         null=True)
    quotable_as_public_case_study = models.NullBooleanField()
    project_shareable = models.NullBooleanField()
    not_shareable_reason = models.TextField(blank=True, null=True)
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
    investor_company = models.ForeignKey(
        'company.Company', related_name='investor_investment_projects',
        null=True, blank=True, on_delete=models.CASCADE
    )
    intermediate_company = models.ForeignKey(
        'company.Company', related_name='intermediate_investment_projects',
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
    referral_source_activity_event = models.CharField(
        max_length=MAX_LENGTH, null=True, blank=True
    )
    fdi_type = models.ForeignKey(
        'metadata.FDIType', related_name='investment_projects', null=True,
        blank=True, on_delete=models.SET_NULL
    )
    non_fdi_type = models.ForeignKey(
        'metadata.NonFDIType', related_name='investment_projects', null=True,
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

    @property
    def project_code(self):
        """A user-friendly project code.

        If a CDMS project code is held, that is returned. Otherwise a Data
        Hub project code beginning with DHP- is returned.
        """
        if self.cdms_project_code:
            return self.cdms_project_code
        try:
            project_num = self.investmentprojectcode.id
            return f'DHP-{project_num:08d}'
        except ObjectDoesNotExist:
            return None


class IProjectValueAbstract(models.Model):
    """The value part of an investment project."""

    class Meta:  # noqa: D101
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
    non_fdi_r_and_d_budget = models.NullBooleanField()
    new_tech_to_uk = models.NullBooleanField()
    export_revenue = models.NullBooleanField()


class IProjectRequirementsAbstract(models.Model):
    """The requirements part of an investment project."""

    class Meta:  # noqa: D101
        abstract = True

    client_requirements = models.TextField(blank=True, null=True)
    # site_decided is deprecated; will be removed
    site_decided = models.NullBooleanField()
    address_line_1 = models.CharField(blank=True, null=True,
                                      max_length=MAX_LENGTH)
    address_line_2 = models.CharField(blank=True, null=True,
                                      max_length=MAX_LENGTH)
    address_line_3 = models.CharField(blank=True, null=True,
                                      max_length=MAX_LENGTH)
    address_line_postcode = models.CharField(blank=True, null=True,
                                             max_length=MAX_LENGTH)
    client_considering_other_countries = models.NullBooleanField()

    uk_company_decided = models.NullBooleanField()
    uk_company = models.ForeignKey(
        'company.Company', related_name='investee_projects',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    competitor_countries = models.ManyToManyField('metadata.Country',
                                                  related_name='+', blank=True)
    uk_region_locations = models.ManyToManyField('metadata.UKRegion',
                                                 related_name='+', blank=True)
    strategic_drivers = models.ManyToManyField(
        'metadata.InvestmentStrategicDriver',
        related_name='investment_projects', blank=True
    )


class IProjectTeamAbstract(models.Model):
    """The team part of an investment project."""

    class Meta:  # noqa: D101
        abstract = True

    project_manager = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True,
        on_delete=models.SET_NULL
    )
    project_assurance_adviser = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True,
        on_delete=models.SET_NULL
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


class InvestmentProject(ArchivableModel, IProjectAbstract,
                        IProjectValueAbstract, IProjectRequirementsAbstract,
                        IProjectTeamAbstract, BaseModel):
    """An investment project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    def __str__(self):
        """Human-readable name for admin section etc."""
        company_name = self.investor_company or 'No company'
        return f'{company_name} – {self.name}'


class InvestmentProjectTeamMember(models.Model):
    """Intermediary M2M model for investment project team members.

    ManyToManyField with through is not used in the InvestmentProject model, because
    it makes working with DRF serialisers difficult (as it would return advisers rather than
    instances of this model).
    """

    investment_project = models.ForeignKey(
        InvestmentProject, on_delete=models.CASCADE, related_name='team_members'
    )
    adviser = models.ForeignKey('company.Advisor', on_delete=models.CASCADE, related_name='+')
    role = models.CharField(max_length=MAX_LENGTH)

    def __str__(self):
        """Human-readable representation."""
        return f'{self.investment_project} – {self.adviser} – {self.role}'

    class Meta:  # noqa: D101
        unique_together = (('investment_project', 'adviser'),)


class InvestmentProjectCode(models.Model):
    """An investment project number used for project codes.

    These are generated for new projects (but not for projects migrated
    from CDMS).

    This is required because Django does not allow AutoFields that are not
    primary keys, and we use UUIDs for primary keys. This model has a
    standard auto-incrementing integer (serial) as a primary key.
    """

    project = models.OneToOneField(InvestmentProject,
                                   on_delete=models.CASCADE)


class IProjectDocument(BaseModel, ArchivableModel):
    """Investment Project Document."""

    BUCKET_PREFIX = 'investment-documents'
    DOC_TYPES = Choices(
        ('actual_land_date', 'Actual land date'),
        ('fdi_type', 'Fdi type'),
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
    doc_type = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=DOC_TYPES,
    )
    filename = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
    )
    document = models.OneToOneField(Document, on_delete=models.PROTECT)

    @property
    def signed_url(self):
        """Generate pre-signed download URL."""
        return self.document.generate_signed_url()

    @property
    def signed_upload_url(self):
        """Generate pre-signed upload URL."""
        return self.document.generate_signed_upload_url()

    class Meta:  # noqa: D101
        verbose_name = 'investment project document'
        verbose_name_plural = 'investment project documents'
        unique_together = (
            ('project', 'doc_type', 'filename'),
        )

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
