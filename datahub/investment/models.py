"""Investment project models."""
import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class IProjectAbstract(models.Model):
    """TODO: document."""

    class Meta:  # noqa: D101
        abstract = True

    name = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField()
    nda_signed = models.BooleanField()
    estimated_land_date = models.DateField(null=True)
    investment_type = models.ForeignKey('metadata.InvestmentType',
                                        related_name='investment_projects')
    phase = models.ForeignKey('metadata.InvestmentProjectPhase',
                              related_name='investment_projects')

    project_code = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    document_link = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    project_shareable = models.BooleanField(default=False)
    anonymous_description = models.TextField(blank=True, null=True)
    not_shareable_reason = models.TextField(blank=True, null=True)

    investor_company = models.ForeignKey(
        'company.Company', related_name='investor_investment_projects', null=True
    )
    intermediate_company = models.ForeignKey(
        'company.Company', related_name='intermediate_investment_projects', null=True
    )
    investment_recipient_company = models.ForeignKey(
        'company.Company', related_name='recipient_investment_projects', null=True
    )
    client_contacts = models.ManyToManyField(
        'company.Contact', related_name='investment_projects', null=True
    )
    client_relationship_manager = models.ForeignKey(
        'company.Advisor', related_name='investment_projects', null=True
    )
    referral_source_advisor = models.ForeignKey(
        'company.Advisor', related_name='referred_investment_projects', null=True
    )
    referral_source_activity = models.ForeignKey(
        'metadata.ReferralSourceActivity', related_name='investment_projects', null=True
    )
    referral_source_activity_website = models.ForeignKey(
        'metadata.ReferralSourceWebsite', related_name='investment_projects', null=True
    )
    referral_source_activity_marketing = models.ForeignKey(
        'metadata.ReferralSourceMarketing', related_name='investment_projects', null=True
    )
    referral_source_activity_event = models.ForeignKey(
        'metadata.Event', related_name='investment_projects', null=True
    )
    fdi_type = models.ForeignKey(
        'metadata.FDIType', related_name='investment_projects', null=True
    )
    non_fdi_type = models.ForeignKey(
        'metadata.NonFDIType', related_name='investment_projects', null=True
    )
    sector = models.ForeignKey('metadata.Sector', related_name='+', null=True)
    business_activity = models.ManyToManyField(
        'metadata.InvestmentBusinessActivity',
        related_name='+'
    )


class IProjectValueAbstract(models.Model):
    """TODO: document."""

    class Meta:  # noqa: D101
        abstract = True

    total_investment = models.DecimalField(null=True, max_digits=19, decimal_places=0)
    foreign_equity_investment = models.DecimalField(null=True, max_digits=19, decimal_places=0)
    government_assistance = models.NullBooleanField()
    number_new_jobs = models.IntegerField(null=True)
    average_salary = models.ForeignKey(
        'metadata.SalaryRange', related_name='+', null=True
    )
    number_safeguarded_jobs = models.IntegerField(null=True)
    r_and_d_budget = models.NullBooleanField()
    non_fdi_r_and_d_budget = models.NullBooleanField()
    new_tech_to_uk = models.NullBooleanField()
    export_revenue = models.NullBooleanField()


class IProjectRequirementsAbstract(models.Model):
    """TODO: document."""

    class Meta:  # noqa: D101
        abstract = True

    client_requirements = models.TextField(blank=True, null=True)
    site_decided = models.NullBooleanField()
    address_line_1 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_2 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_3 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_postcode = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)

    competitor_countries = models.ManyToManyField('metadata.Country', related_name='+')
    uk_region_locations = models.ManyToManyField('metadata.UKRegion', related_name='+')
    strategic_drivers = models.ManyToManyField(
        'metadata.InvestmentStrategicDriver', related_name='investment_projects'
    )


class IProjectTeamAbstract(models.Model):
    """TODO: document."""

    class Meta:  # noqa: D101
        abstract = True

    project_manager = models.ForeignKey(
        'company.Advisor', null=True, related_name='+'
    )
    project_assurance_advisor = models.ForeignKey(
        'company.Advisor', null=True, related_name='+'
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


class InvestmentProject(IProjectAbstract, IProjectValueAbstract, IProjectRequirementsAbstract,
                        IProjectTeamAbstract, BaseModel):
    """TODO: document."""

    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
