"""Investment serialisers for views."""

from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Advisor, Company, Contact
from datahub.core.constants import InvestmentProjectPhase
from datahub.core.serializers import NestedRelatedField
from datahub.investment.models import InvestmentProject
from datahub.investment.validate import get_validators


class IProjectSerializer(serializers.ModelSerializer):
    """Serialiser for investment project endpoints."""

    project_code = serializers.CharField(read_only=True)

    investment_type = NestedRelatedField(meta_models.InvestmentType)
    phase = NestedRelatedField(meta_models.InvestmentProjectPhase,
                               required=False)
    investor_company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    intermediate_company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    investment_recipient_company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    client_contacts = NestedRelatedField(Contact, many=True, required=False)

    client_relationship_manager = NestedRelatedField(
        Advisor, required=False, allow_null=True,
        extra_fields=('first_name', 'last_name')
    )
    referral_source_advisor = NestedRelatedField(
        Advisor, required=False, allow_null=True,
        extra_fields=('first_name', 'last_name')
    )
    referral_source_activity = NestedRelatedField(
        meta_models.ReferralSourceActivity, required=False, allow_null=True
    )
    referral_source_activity_website = NestedRelatedField(
        meta_models.ReferralSourceWebsite, required=False, allow_null=True
    )
    referral_source_activity_marketing = NestedRelatedField(
        meta_models.ReferralSourceMarketing, required=False, allow_null=True
    )
    referral_source_activity_event = NestedRelatedField(
        meta_models.Event, required=False, allow_null=True
    )
    fdi_type = NestedRelatedField(
        meta_models.FDIType, required=False, allow_null=True
    )
    non_fdi_type = NestedRelatedField(
        meta_models.NonFDIType, required=False, allow_null=True
    )
    sector = NestedRelatedField(
        meta_models.Sector, required=False, allow_null=True
    )
    business_activities = NestedRelatedField(
        meta_models.InvestmentBusinessActivity, many=True, required=False
    )
    project_section_complete = serializers.BooleanField(read_only=True)

    def validate(self, data):
        """Validates the object after individual fields have been validated.

        Performs phase-dependent validation of the different sections.
        """
        previous_phase = (self.instance.phase if self.instance else
                          InvestmentProjectPhase.prospect.value)
        desired_phase = data.get('phase', previous_phase)
        errors = {}

        for phase, validator in get_validators():
            if desired_phase.order >= phase.order:
                errors.update(validator(
                    instance=self.instance, update_data=data
                ))

        if errors:
            raise serializers.ValidationError(errors)
        return data

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'id', 'name', 'project_code', 'description',
            'nda_signed', 'estimated_land_date', 'project_shareable',
            'anonymous_description', 'not_shareable_reason',
            'investment_type', 'phase', 'investor_company',
            'intermediate_company', 'investment_recipient_company',
            'client_contacts', 'client_relationship_manager',
            'referral_source_advisor', 'referral_source_activity',
            'referral_source_activity_website',
            'referral_source_activity_marketing',
            'referral_source_activity_event', 'fdi_type', 'non_fdi_type',
            'sector', 'business_activities', 'project_section_complete'
        )


class IProjectValueSerializer(serializers.ModelSerializer):
    """Serialiser for investment project value objects."""

    average_salary = NestedRelatedField(
        meta_models.SalaryRange, required=False,
        allow_null=True
    )
    value_complete = serializers.BooleanField(read_only=True)

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'total_investment', 'foreign_equity_investment',
            'government_assistance', 'number_new_jobs', 'average_salary',
            'number_safeguarded_jobs', 'r_and_d_budget',
            'non_fdi_r_and_d_budget', 'new_tech_to_uk', 'export_revenue',
            'value_complete', 'client_cannot_provide_total_investment',
            'client_cannot_provide_foreign_investment'
        )


class IProjectRequirementsSerializer(serializers.ModelSerializer):
    """Serialiser for investment project requirements objects."""

    competitor_countries = NestedRelatedField(
        meta_models.Country, many=True, required=False
    )
    uk_region_locations = NestedRelatedField(
        meta_models.UKRegion, many=True, required=False
    )
    strategic_drivers = NestedRelatedField(
        meta_models.InvestmentStrategicDriver, many=True, required=False
    )
    requirements_complete = serializers.BooleanField(read_only=True)
    uk_company = NestedRelatedField(Company, required=False, allow_null=True)

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'client_requirements', 'site_decided', 'address_line_1',
            'address_line_2', 'address_line_3', 'address_line_postcode',
            'competitor_countries', 'uk_region_locations',
            'strategic_drivers', 'client_considering_other_countries',
            'uk_company', 'requirements_complete'
        )


class IProjectTeamSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team objects."""

    project_manager = NestedRelatedField(
        Advisor, required=False, allow_null=True,
        extra_fields=('first_name', 'last_name')
    )
    project_assurance_advisor = NestedRelatedField(
        Advisor, required=False, allow_null=True,
        extra_fields=('first_name', 'last_name')
    )
    project_manager_team = NestedRelatedField(
        meta_models.Team, read_only=True
    )
    project_assurance_team = NestedRelatedField(
        meta_models.Team, read_only=True
    )

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'project_manager', 'project_assurance_advisor',
            'project_manager_team', 'project_assurance_team'
        )
