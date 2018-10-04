"""Investment serialisers for views."""
from collections import Counter
from functools import partial

from django.utils.translation import ugettext_lazy
from rest_framework import serializers

import datahub.metadata.models as meta_models
from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.constants import InvestmentProjectStage
from datahub.core.serializers import NestedRelatedField, PermittedFieldsModelSerializer
from datahub.core.validate_utils import DataCombiner
from datahub.investment.models import (
    InvestmentDeliveryPartner,
    InvestmentProject,
    InvestmentProjectPermission,
    InvestmentProjectStageLog,
    InvestmentProjectTeamMember,
    InvestorType,
    Involvement,
    SpecificProgramme,
)
from datahub.investment.validate import validate

CORE_FIELDS = (
    'id',
    'incomplete_fields',
    'name',
    'project_code',
    'description',
    'anonymous_description',
    'allow_blank_estimated_land_date',
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
    'sector',
    'business_activities',
    'other_business_activity',
    'archived',
    'archived_documents_url_path',
    'archived_on',
    'archived_reason',
    'archived_by',
    'created_on',
    'modified_on',
    'comments',
)

VALUE_FIELDS = (
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
    'client_cannot_provide_foreign_investment',
)

REQUIREMENTS_FIELDS = (
    'client_requirements',
    'site_decided',
    'address_1',
    'address_2',
    'address_town',
    'address_postcode',
    'competitor_countries',
    'allow_blank_possible_uk_regions',
    'uk_region_locations',
    'actual_uk_regions',
    'delivery_partners',
    'strategic_drivers',
    'client_considering_other_countries',
    'uk_company_decided',
    'uk_company',
    'requirements_complete',
)

TEAM_FIELDS = (
    'project_manager',
    'project_assurance_adviser',
    'project_manager_team',
    'project_assurance_team',
    'team_complete',
    'team_members',
)

SPI_FIELDS = (
    'project_arrived_in_triage_on',
    'proposal_deadline',
    'stage_log',
)

ALL_FIELDS = CORE_FIELDS + VALUE_FIELDS + REQUIREMENTS_FIELDS + TEAM_FIELDS + SPI_FIELDS


class NestedIProjectTeamMemberSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team members when nested in the main investment
    project object.

    Used to exclude the investment project from the serialised representation.
    """

    adviser = NestedAdviserField()

    class Meta:
        model = InvestmentProjectTeamMember
        fields = ('adviser', 'role')


class NestedInvestmentProjectStageLogSerializer(serializers.ModelSerializer):
    """Serialiser for investment project stage log."""

    stage = NestedRelatedField(meta_models.InvestmentProjectStage, read_only=True)
    created_on = serializers.DateTimeField(read_only=True)

    class Meta:
        model = InvestmentProjectStageLog
        fields = ('stage', 'created_on')


class IProjectSerializer(PermittedFieldsModelSerializer):
    """Serialiser for investment project endpoints."""

    default_error_messages = {
        'only_pm_or_paa_can_move_to_verify_win': ugettext_lazy(
            'Only the Project Manager or Project Assurance Adviser can move the project'
            ' to the ‘Verify win’ stage.',
        ),
        'only_ivt_can_move_to_won': ugettext_lazy(
            'Only the Investment Verification Team can move the project to the ‘Won’ stage.',
        ),
    }

    incomplete_fields = serializers.SerializerMethodField()
    project_code = serializers.CharField(read_only=True)
    investment_type = NestedRelatedField(meta_models.InvestmentType)
    stage = NestedRelatedField(meta_models.InvestmentProjectStage, required=False)
    country_lost_to = NestedRelatedField(meta_models.Country, required=False, allow_null=True)
    investor_company = NestedRelatedField(Company, required=True, allow_null=False)
    investor_company_country = NestedRelatedField(meta_models.Country, read_only=True)
    investor_type = NestedRelatedField(InvestorType, required=False, allow_null=True)
    intermediate_company = NestedRelatedField(Company, required=False, allow_null=True)
    level_of_involvement = NestedRelatedField(Involvement, required=False, allow_null=True)
    specific_programme = NestedRelatedField(SpecificProgramme, required=False, allow_null=True)
    client_contacts = NestedRelatedField(
        Contact, many=True, required=True, allow_null=False, allow_empty=False,
    )

    client_relationship_manager = NestedAdviserField(required=True, allow_null=False)
    client_relationship_manager_team = NestedRelatedField(meta_models.Team, read_only=True)
    referral_source_adviser = NestedAdviserField(required=True, allow_null=False)
    referral_source_activity = NestedRelatedField(
        meta_models.ReferralSourceActivity, required=True, allow_null=False,
    )
    referral_source_activity_website = NestedRelatedField(
        meta_models.ReferralSourceWebsite, required=False, allow_null=True,
    )
    referral_source_activity_marketing = NestedRelatedField(
        meta_models.ReferralSourceMarketing, required=False, allow_null=True,
    )
    fdi_type = NestedRelatedField(meta_models.FDIType, required=False, allow_null=True)
    sector = NestedRelatedField(meta_models.Sector, required=True, allow_null=False)
    business_activities = NestedRelatedField(
        meta_models.InvestmentBusinessActivity, many=True, required=True,
        allow_null=False, allow_empty=False,
    )
    archived_by = NestedAdviserField(read_only=True)

    # Value fields
    fdi_value = NestedRelatedField(meta_models.FDIValue, required=False, allow_null=True)
    average_salary = NestedRelatedField(
        meta_models.SalaryRange, required=False, allow_null=True,
    )
    value_complete = serializers.SerializerMethodField()
    associated_non_fdi_r_and_d_project = NestedRelatedField(
        InvestmentProject, required=False, allow_null=True, extra_fields=('name', 'project_code'),
    )

    # Requirements fields
    competitor_countries = NestedRelatedField(meta_models.Country, many=True, required=False)
    # Note: uk_region_locations is the possible UK regions at the start of the project (not the
    # actual/final UK regions at the end of the project)
    uk_region_locations = NestedRelatedField(meta_models.UKRegion, many=True, required=False)
    actual_uk_regions = NestedRelatedField(meta_models.UKRegion, many=True, required=False)
    delivery_partners = NestedRelatedField(InvestmentDeliveryPartner, many=True, required=False)
    strategic_drivers = NestedRelatedField(
        meta_models.InvestmentStrategicDriver, many=True, required=False,
    )
    uk_company = NestedRelatedField(Company, required=False, allow_null=True)
    requirements_complete = serializers.SerializerMethodField()

    # Team fields
    project_manager = NestedAdviserField(required=False, allow_null=True)
    project_assurance_adviser = NestedAdviserField(required=False, allow_null=True)
    project_manager_team = NestedRelatedField(meta_models.Team, read_only=True)
    project_assurance_team = NestedRelatedField(meta_models.Team, read_only=True)
    team_members = NestedIProjectTeamMemberSerializer(many=True, read_only=True)
    team_complete = serializers.SerializerMethodField()

    # SPI fields
    project_arrived_in_triage_on = serializers.DateField(required=False, allow_null=True)
    proposal_deadline = serializers.DateField(required=False, allow_null=True)
    stage_log = NestedInvestmentProjectStageLogSerializer(many=True, read_only=True)

    def validate(self, data):
        """Validates the object after individual fields have been validated.

        Performs stage-dependent validation of the different sections.

        When transitioning stage, all fields required for the new stage are validated. In other
        cases, only the fields being modified are validated.  If a project ends up in an
        invalid state, this avoids the user being unable to rectify the situation.
        """
        if not self.instance:
            # Required for validation as DRF does not allow defaults for read-only fields
            data['allow_blank_estimated_land_date'] = False
            data['allow_blank_possible_uk_regions'] = False

        self._check_if_investment_project_can_be_moved_to_verify_win(data)
        self._check_if_investment_project_can_be_moved_to_won(data)

        fields = None
        if self.partial and 'stage' not in data:
            fields = data.keys()
        errors = validate(self.instance, data, fields=fields)

        if errors:
            raise serializers.ValidationError(errors)

        self._update_status(data)

        return data

    def _check_if_investment_project_can_be_moved_to_verify_win(self, data):
        # only project manager or project assurance adviser can move a project to verify win
        if self.instance and 'stage' in data:
            current_user_id = self.context['current_user'].id
            allowed_users_ids = (
                self.instance.project_manager_id, self.instance.project_assurance_adviser_id,
            )

            if (
                str(data['stage'].id) == InvestmentProjectStage.verify_win.value.id
                and self.instance.stage.order < data['stage'].order
                and current_user_id not in allowed_users_ids
            ):
                errors = {
                    'stage': self.default_error_messages['only_pm_or_paa_can_move_to_verify_win'],
                }
                raise serializers.ValidationError(errors)

    def _check_if_investment_project_can_be_moved_to_won(self, data):
        # Investment Verification Team can only move a project to won
        if self.instance and 'stage' in data:
            current_user = self.context['current_user']
            permission_name = f'investment.{InvestmentProjectPermission.change_stage_to_won}'
            if (
                str(data['stage'].id) == InvestmentProjectStage.won.value.id
                and self.instance.stage.order < data['stage'].order
                and not current_user.has_perm(permission_name)
            ):
                errors = {
                    'stage': self.default_error_messages['only_ivt_can_move_to_won'],
                }
                raise serializers.ValidationError(errors)

    def get_incomplete_fields(self, instance):
        """Returns the names of the fields that still need to be completed in order to
        move to the next stage.
        """
        return tuple(validate(instance=instance, next_stage=True))

    def get_value_complete(self, instance):
        """Whether the value fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=VALUE_FIELDS, next_stage=True,
        )

    def get_requirements_complete(self, instance):
        """Whether the requirements fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=REQUIREMENTS_FIELDS, next_stage=True,
        )

    def get_team_complete(self, instance):
        """Whether the team fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=TEAM_FIELDS, next_stage=True,
        )

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
        fields = ALL_FIELDS
        # DRF defaults to required=False even though this field is non-nullable
        extra_kwargs = {
            'likelihood_of_landing': {'min_value': 0, 'max_value': 100},
        }
        permissions = {
            f'investment.{InvestmentProjectPermission.view_investmentproject_document}':
                'archived_documents_url_path',
        }
        read_only_fields = (
            'allow_blank_estimated_land_date',
            'allow_blank_possible_uk_regions',
            'archived',
            'archived_on',
            'archived_reason',
            'archived_documents_url_path',
            'comments',
        )


NestedInvestmentProjectField = partial(
    NestedRelatedField, InvestmentProject,
    extra_fields=('name', 'project_code'),
)


class IProjectTeamMemberListSerializer(serializers.ListSerializer):
    """Team member list serialiser that adds validation for duplicates."""

    default_error_messages = {
        'duplicate_adviser': ugettext_lazy(
            'You cannot add the same adviser as a team member more than once.',
        ),
    }

    def update(self, instances, validated_data):
        """
        Performs an update i.e. replaces all team members.

        Based on example code in DRF documentation for ListSerializer.
        """
        old_advisers_mapping = {team_member.adviser.id: team_member for team_member in
                                instances}
        new_advisers_mapping = {team_member['adviser'].id: team_member for team_member in
                                validated_data}

        # Create new team members and update existing ones
        ret = []
        for adviser_id, new_team_member_data in new_advisers_mapping.items():
            team_member = old_advisers_mapping.get(adviser_id, None)
            if team_member is None:
                ret.append(self.child.create(new_team_member_data))
            else:
                ret.append(self.child.update(team_member, new_team_member_data))

        # Delete removed team members
        for adviser_id in old_advisers_mapping.keys() - new_advisers_mapping.keys():
            old_advisers_mapping[adviser_id].delete()

        return ret

    def run_validation(self, data=serializers.empty):
        """
        Validates that there are no duplicate advisers (to avoid a 500 error).

        Unfortunately, overriding validate() results in a error dict being returned and the errors
        being placed in non_field_errors. Hence, run_validation() is overridden instead (to get
        the expected behaviour of an error list being returned, with each entry corresponding
        to each item in the request body).
        """
        value = super().run_validation(data)

        counts = Counter(team_member['adviser'].id for team_member in value)
        if len(counts) < len(value):
            errors = []
            for item in value:
                item_errors = {}
                if counts[item['adviser'].id] > 1:
                    item_errors['adviser'] = [self.error_messages['duplicate_adviser']]
                errors.append(item_errors)
            raise serializers.ValidationError(errors)

        return value


class IProjectTeamMemberSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team members."""

    investment_project = NestedRelatedField(InvestmentProject)
    adviser = NestedAdviserField()

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        Initialises a many-item instance of the serialiser using custom logic.

        This disables the unique together validator in the child serialiser, as it's incompatible
        with many-item update operations (as it mistakenly fails existing rows).
        """
        child = cls(context=kwargs.get('context'), validators=())
        return IProjectTeamMemberListSerializer(child=child, *args, **kwargs)

    class Meta:
        model = InvestmentProjectTeamMember
        fields = ('investment_project', 'adviser', 'role')
