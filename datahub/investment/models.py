"""Investment project models."""
from django.conf import settings
from django.db import models

from datahub.core.models import ArchivableModel, BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class IProjectAbstract(models.Model):
    """TODO"""

    class Meta:  # noqa: D101
        abstract = True

    name = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField()
    nda_signed = models.BooleanField()
    estimated_land_date = models.DateField(null=True)
    investment_type = models.ForeignKey('metadata.InvestmentType')

    project_code = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    document_link = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    project_shareable = models.BooleanField(default=False)
    anonymous_description = models.TextField(blank=True, null=True)
    not_shareable_reason = models.TextField(blank=True, null=True)

    phase = models.ForeignKey('metadata.InvestmentProjectPhase', related_name='+')
    investor_company = models.ForeignKey(
        'company.Company', related_name="investor_investment_projects", null=True
    )
    investment_recipient_company = models.ForeignKey(
        'company.Company', related_name="recipient_investment_projects", null=True
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
    referral_source_activity = models.ForeignKey('metadata.ReferralSourceActivity', null=True)
    referral_source_activity_website = models.ForeignKey(
        'metadata.ReferralSourceActivity', related='investment_projects', null=True
    )
    referral_source_activity_marketing = models.ForeignKey(
        'metadata.ReferralSourceActivity', related='investment_projects', null=True
    )
    referral_source_activity_event = models.ForeignKey(
        'metadata.Event', related='investment_projects', null=True
    )
    fdi_type = models.ForeignKey(
        'metadata.FDIType', related='investment_projects', null=True
    )
    non_fdi_type = models.ForeignKey(
        'metadata.NonFDIType', related='investment_projects', null=True
    )
    sector = models.ForeignKey('metadata.Sectors', related_name='+', null=True)
    business_activity = models.ForeignKey('metadata.InvestmentBusinessActivity', related_name='+')


class IProjectValueAbstract(models.Model):
    """TODO"""

    class Meta:  # noqa: D101
        abstract = True

    total_investment = models.DecimalField(null=True)
    foreign_equity_investment = models.DecimalField(null=True)
    government_assistance = models.BooleanField(null=True)
    number_new_jobs = models.IntegerField(null=True)
    number_safeguarded_jobs = models.IntegerField(null=True)
    r_and_d_budget = models.BooleanField(null=True)
    non_fdi_r_and_d_budget = models.BooleanField(null=True)
    new_tech_to_uk = models.BooleanField(null=True)
    export_revenue = models.BooleanField(null=True)


class IProjectRequirementsAbstract(models.Model):
    """TODO"""

    class Meta:  # noqa: D101
        abstract = True

    client_requirements = models.TextField(blank=True, null=True)
    site_decided = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_1 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_2 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_3 = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)
    address_line_postcode = models.CharField(blank=True, null=True, max_length=MAX_LENGTH)

    competitor_countries = models.ManyToManyField('metadata.Country', related_name='+')
    uk_region_locations = models.ManyToManyField('metadata.UKRegion', related_name='+')
    strategic_drivers = models.ManyToManyField()  # TODO


class IProjectTeamAbstract(models.Model):
    """TODO"""

    class Meta:  # noqa: D101
        abstract = True

    project_manager_team = models.ForeignKey('company.AdvisorTeam', null=True)  # TODO
    project_manager = models.ForeignKey('company.Advisor', null=True)
    project_assurance_team = models.ForeignKey('company.AdvisorTeam', null=True)  # TODO
    project_assurance = models.ForeignKey('company.Advisor', null=True)


class InvestmentProject(IProjectAbstract, IProjectValueAbstract, IProjectRequirementsAbstract,
                        IProjectTeamAbstract, ArchivableModel, BaseModel):
    """TODO"""
