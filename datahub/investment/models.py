"""Investment project models."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from datahub.core.constants import InvestmentProjectPhase
from datahub.core.models import BaseModel
from datahub.investment.validate import get_incomplete_project_fields

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class IProjectAbstract(models.Model):
    """The core part of an investment project."""

    class Meta:  # noqa: D101
        abstract = True

    name = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField()
    nda_signed = models.BooleanField()
    estimated_land_date = models.DateField()
    investment_type = models.ForeignKey('metadata.InvestmentType',
                                        related_name='investment_projects')

    cdms_project_code = models.CharField(max_length=MAX_LENGTH, blank=True,
                                         null=True)
    project_shareable = models.NullBooleanField()
    anonymous_description = models.TextField(blank=True, null=True)
    not_shareable_reason = models.TextField(blank=True, null=True)

    phase = models.ForeignKey('metadata.InvestmentProjectPhase',
                              related_name='investment_projects',
                              default=InvestmentProjectPhase.prospect.value.id)
    investor_company = models.ForeignKey(
        'company.Company', related_name='investor_investment_projects',
        null=True, blank=True
    )
    intermediate_company = models.ForeignKey(
        'company.Company', related_name='intermediate_investment_projects',
        null=True, blank=True
    )
    investment_recipient_company = models.ForeignKey(
        'company.Company', related_name='recipient_investment_projects',
        null=True, blank=True
    )
    client_contacts = models.ManyToManyField(
        'company.Contact', related_name='investment_projects', blank=True
    )
    client_relationship_manager = models.ForeignKey(
        'company.Advisor', related_name='investment_projects', null=True,
        blank=True
    )
    referral_source_advisor = models.ForeignKey(
        'company.Advisor', related_name='referred_investment_projects',
        null=True, blank=True
    )
    referral_source_activity = models.ForeignKey(
        'metadata.ReferralSourceActivity', related_name='investment_projects',
        null=True, blank=True
    )
    referral_source_activity_website = models.ForeignKey(
        'metadata.ReferralSourceWebsite', related_name='investment_projects',
        null=True, blank=True
    )
    referral_source_activity_marketing = models.ForeignKey(
        'metadata.ReferralSourceMarketing', related_name='investment_projects',
        null=True, blank=True
    )
    referral_source_activity_event = models.ForeignKey(
        'metadata.Event', related_name='investment_projects', null=True,
        blank=True
    )
    fdi_type = models.ForeignKey(
        'metadata.FDIType', related_name='investment_projects', null=True,
        blank=True
    )
    non_fdi_type = models.ForeignKey(
        'metadata.NonFDIType', related_name='investment_projects', null=True,
        blank=True
    )
    sector = models.ForeignKey('metadata.Sector', related_name='+', null=True,
                               blank=True)
    business_activity = models.ManyToManyField(
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
        return 'DHP-{:08d}'.format(self.investmentprojectcode.id)

    @property
    def project_section_complete(self):
        """Whether the project section is complete."""
        return not get_incomplete_project_fields(instance=self)


class IProjectValueAbstract(models.Model):
    """The value part of an investment project."""

    class Meta:  # noqa: D101
        abstract = True

    client_cannot_provide_total_investment = models.NullBooleanField()
    total_investment = models.DecimalField(null=True, max_digits=19,
                                           decimal_places=0, blank=True)
    client_cannot_provide_foreign_investment = models.NullBooleanField()
    foreign_equity_investment = models.DecimalField(
        null=True, max_digits=19, decimal_places=0, blank=True
    )
    government_assistance = models.NullBooleanField()
    number_new_jobs = models.IntegerField(null=True, blank=True)
    average_salary = models.ForeignKey(
        'metadata.SalaryRange', related_name='+', null=True, blank=True
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

    uk_company = models.ForeignKey(
        'company.Company', related_name='investee_projects',
        null=True, blank=True
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
        'company.Advisor', null=True, related_name='+', blank=True
    )
    project_assurance_advisor = models.ForeignKey(
        'company.Advisor', null=True, related_name='+', blank=True
    )

    @property
    def project_manager_team(self):
        """The DIT team associated with the project manager."""
        if self.project_manager:
            return self.project_manager.dit_team
        return None

    @property
    def project_assurance_team(self):
        """The DIT team associated with the project assurance advisor."""
        if self.project_assurance_advisor:
            return self.project_assurance_advisor.dit_team
        return None


class InvestmentProject(IProjectAbstract, IProjectValueAbstract,
                        IProjectRequirementsAbstract,
                        IProjectTeamAbstract, BaseModel):
    """An investment project."""

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)


class InvestmentProjectCode(models.Model):
    """An investment project number used for project codes.

    These are generated for new projects (but not for projects migrated
    from CDMS).

    This is required because Django does not allow AutoFields that are not
    primary keys, and we use UUIDs for primary keys. This model has a
    standard auto-incrementing integer (serial) as a primary key.
    """

    project = models.OneToOneField(InvestmentProject)


@receiver(post_save, sender=InvestmentProject)
def project_post_save(sender, **kwargs):
    """Creates a project code for investment projects on creation.

    Projects with a CDMS project code do not get a new project code.
    """
    instance = kwargs['instance']
    created = kwargs['created']
    raw = kwargs['raw']
    if created and not raw and not instance.cdms_project_code:
        InvestmentProjectCode.objects.create(project=instance)
