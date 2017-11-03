"""Investment serialisers for views."""

from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.constants import InvestmentProjectStage
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner
from datahub.investment.models import (
    InvestmentProject,
    InvestmentProjectTeamMember,
    InvestorType,
    Involvement,
    IProjectDocument,
    SpecificProgramme
)
from datahub.investment.validate import validate


class IProjectSummarySerializer(serializers.ModelSerializer):
    """Serialiser for investment project endpoints."""

    incomplete_fields = serializers.SerializerMethodField()
    project_code = serializers.CharField(read_only=True)
    investment_type = NestedRelatedField(meta_models.InvestmentType)
    stage = NestedRelatedField(meta_models.InvestmentProjectStage, required=False)
    country_lost_to = NestedRelatedField(meta_models.Country, required=False, allow_null=True)
    investor_company = NestedRelatedField(Company, required=True, allow_null=False)
    investor_company_country = NestedRelatedField(
        meta_models.Country, read_only=True
    )
    investor_type = NestedRelatedField(InvestorType, required=False, allow_null=True)
    intermediate_company = NestedRelatedField(Company, required=False, allow_null=True)
    level_of_involvement = NestedRelatedField(Involvement, required=False, allow_null=True)
    specific_programme = NestedRelatedField(SpecificProgramme, required=False, allow_null=True)
    client_contacts = NestedRelatedField(
        Contact, many=True, required=True, allow_null=False, allow_empty=False
    )

    client_relationship_manager = NestedAdviserField(required=True, allow_null=False)
    client_relationship_manager_team = NestedRelatedField(
        meta_models.Team, read_only=True
    )
    referral_source_adviser = NestedAdviserField(required=True, allow_null=False)
    referral_source_activity = NestedRelatedField(
        meta_models.ReferralSourceActivity, required=True, allow_null=False
    )
    referral_source_activity_website = NestedRelatedField(
        meta_models.ReferralSourceWebsite, required=False, allow_null=True
    )
    referral_source_activity_marketing = NestedRelatedField(
        meta_models.ReferralSourceMarketing, required=False, allow_null=True
    )
    fdi_type = NestedRelatedField(meta_models.FDIType, required=False, allow_null=True)
    non_fdi_type = NestedRelatedField(meta_models.NonFDIType, required=False, allow_null=True)
    sector = NestedRelatedField(meta_models.Sector, required=True, allow_null=False)
    business_activities = NestedRelatedField(
        meta_models.InvestmentBusinessActivity, many=True, required=True,
        allow_null=False, allow_empty=False
    )
    archived_by = NestedAdviserField(read_only=True)

    def get_incomplete_fields(self, instance):
        """Returns the names of the fields that still need to be completed in order to
        move to the next stage.
        """
        return tuple(validate(instance=instance, next_stage=True))

    def validate(self, data):
        """Validates the object after individual fields have been validated.

        Performs stage-dependent validation of the different sections.

        When transitioning stage, all fields required for the new stage are validated. In other
        cases, only the fields being modified are validated.  If a project ends up in an
        invalid state, this avoids the user being unable to rectify the situation.
        """
        fields = None
        if self.partial and 'stage' not in data:
            fields = data.keys()
        errors = validate(self.instance, data, fields=fields)

        if errors:
            raise serializers.ValidationError(errors)

        self._update_status(data)

        return data

    def _update_status(self, data):
        """Updates the project status when the stage changes to or from Won."""
        old_stage = self.instance.stage if self.instance else None
        new_stage = data.get('stage')

        if not new_stage or new_stage == old_stage:
            return

        combiner = DataCombiner(instance=self.instance, update_data=data)
        new_status = combiner.get_value('status')

        if str(new_stage.id) == InvestmentProjectStage.won.value.id:
            data['status'] = InvestmentProject.STATUSES.won
        elif (old_stage and str(old_stage.id) == InvestmentProjectStage.won.value.id and
                new_status == InvestmentProject.STATUSES.won):
            data['status'] = InvestmentProject.STATUSES.ongoing

    class Meta:
        model = InvestmentProject
        fields = (
            'id',
            'incomplete_fields',
            'name',
            'project_code',
            'description',
            'anonymous_description',
            'estimated_land_date',
            'actual_land_date',
            'quotable_as_public_case_study',
            'likelihood_of_landing',
            'priority',
            'approved_commitment_to_invest',
            'approved_fdi',
            'approved_good_value',
            'approved_high_value',
            'approved_landed',
            'approved_non_fdi',
            'investment_type',
            'stage',
            'status',
            'reason_delayed',
            'reason_abandoned',
            'date_abandoned',
            'reason_lost',
            'date_lost',
            'country_lost_to',
            'investor_company',
            'investor_type',
            'investor_company_country',
            'intermediate_company',
            'level_of_involvement',
            'specific_programme',
            'client_contacts',
            'client_relationship_manager',
            'client_relationship_manager_team',
            'referral_source_adviser',
            'referral_source_activity',
            'referral_source_activity_website',
            'referral_source_activity_marketing',
            'referral_source_activity_event',
            'fdi_type',
            'non_fdi_type',
            'sector',
            'business_activities',
            'other_business_activity',
            'archived',
            'archived_on',
            'archived_reason',
            'archived_by',
            'created_on',
            'modified_on'
        )
        # DRF defaults to required=False even though this field is
        # non-nullable
        extra_kwargs = {
            'likelihood_of_landing': {'min_value': 0, 'max_value': 100},
            'archived': {'read_only': True},
            'archived_on': {'read_only': True},
            'archived_reason': {'read_only': True}
        }


class IProjectValueSerializer(serializers.ModelSerializer):
    """Serialiser for investment project value objects."""

    fdi_value = NestedRelatedField(meta_models.FDIValue, required=False, allow_null=True)
    average_salary = NestedRelatedField(
        meta_models.SalaryRange, required=False,
        allow_null=True
    )
    value_complete = serializers.SerializerMethodField()
    associated_non_fdi_r_and_d_project = NestedRelatedField(
        InvestmentProject, required=False, allow_null=True, extra_fields=('name', 'project_code')
    )

    def get_value_complete(self, instance):
        """Whether the value fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=IProjectValueSerializer.Meta.fields, next_stage=True
        )

    class Meta:
        model = InvestmentProject
        fields = (
            'fdi_value',
            'total_investment',
            'foreign_equity_investment',
            'government_assistance',
            'some_new_jobs',
            'number_new_jobs',
            'will_new_jobs_last_two_years',
            'average_salary',
            'number_safeguarded_jobs',
            'r_and_d_budget',
            'non_fdi_r_and_d_budget',
            'associated_non_fdi_r_and_d_project',
            'new_tech_to_uk',
            'export_revenue',
            'value_complete',
            'client_cannot_provide_total_investment',
            'client_cannot_provide_foreign_investment'
        )


class IProjectRequirementsSerializer(serializers.ModelSerializer):
    """Serialiser for investment project requirements objects."""

    competitor_countries = NestedRelatedField(meta_models.Country, many=True, required=False)
    uk_region_locations = NestedRelatedField(meta_models.UKRegion, many=True, required=False)
    strategic_drivers = NestedRelatedField(
        meta_models.InvestmentStrategicDriver, many=True, required=False
    )
    uk_company = NestedRelatedField(Company, required=False, allow_null=True)
    requirements_complete = serializers.SerializerMethodField()

    def get_requirements_complete(self, instance):
        """Whether the requirements fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=IProjectRequirementsSerializer.Meta.fields, next_stage=True
        )

    class Meta:
        model = InvestmentProject
        fields = (
            'client_requirements',
            'site_decided',  # deprecated; will be removed
            'address_1',
            'address_2',
            'address_town',
            'address_postcode',
            'competitor_countries',
            'uk_region_locations',
            'strategic_drivers',
            'client_considering_other_countries',
            'uk_company_decided',
            'uk_company',
            'requirements_complete'
        )


class IProjectTeamMemberSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team members."""

    investment_project = NestedRelatedField(InvestmentProject)
    adviser = NestedAdviserField()

    class Meta:
        model = InvestmentProjectTeamMember
        fields = ('investment_project', 'adviser', 'role')


class NestedIProjectTeamMemberSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team members when nested in the main investment
    project object.

    Used to exclude the investment project from the serialised representation.
    """

    adviser = NestedAdviserField()

    class Meta:
        model = InvestmentProjectTeamMember
        fields = ('adviser', 'role')


class IProjectTeamSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team objects."""

    project_manager = NestedAdviserField(required=False, allow_null=True)
    project_assurance_adviser = NestedAdviserField(required=False, allow_null=True)
    project_manager_team = NestedRelatedField(meta_models.Team, read_only=True)
    project_assurance_team = NestedRelatedField(meta_models.Team, read_only=True)
    team_members = NestedIProjectTeamMemberSerializer(many=True, read_only=True)
    team_complete = serializers.SerializerMethodField()

    def get_team_complete(self, instance):
        """Whether the team fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=IProjectTeamSerializer.Meta.fields, next_stage=True
        )

    class Meta:
        model = InvestmentProject
        fields = (
            'project_manager',
            'project_assurance_adviser',
            'project_manager_team',
            'project_assurance_team',
            'team_complete',
            'team_members'
        )


class IProjectSerializer(IProjectSummarySerializer, IProjectValueSerializer,
                         IProjectRequirementsSerializer, IProjectTeamSerializer):
    """Serialiser for investment projects, used with the new unified investment endpoint."""

    class Meta:
        model = InvestmentProject
        fields = (
            IProjectSummarySerializer.Meta.fields
            + IProjectValueSerializer.Meta.fields
            + IProjectRequirementsSerializer.Meta.fields
            + IProjectTeamSerializer.Meta.fields
        )
        extra_kwargs = IProjectSummarySerializer.Meta.extra_kwargs


class IProjectDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Investment Project Documents."""

    project = NestedRelatedField(
        InvestmentProject,
    )

    class Meta:
        model = IProjectDocument
        fields = (
            'id',
            'project',
            'doc_type',
            'filename',
            'signed_url',
        )
        read_only_fields = ('signed_url', )

    def create(self, validated_data):
        """Create investment document."""
        return IProjectDocument.create_from_declaration_request(
            project=validated_data['project'],
            field=validated_data['doc_type'],
            filename=validated_data['filename'],
        )


class UploadStatusSerializer(serializers.Serializer):
    """Serializer for upload status endpoints."""

    status = serializers.ChoiceField(choices=('success',))
