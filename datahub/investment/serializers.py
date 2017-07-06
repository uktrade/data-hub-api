"""Investment serialisers for views."""

from rest_framework import serializers
from reversion.models import Version

import datahub.metadata.models as meta_models
from datahub.company.models import Advisor, Company, Contact
from datahub.core.serializers import NestedRelatedField
from datahub.investment.models import InvestmentProject, IProjectDocument
from datahub.investment.validate import validate


class IProjectSerializer(serializers.ModelSerializer):
    """Serialiser for investment project endpoints."""

    project_code = serializers.CharField(read_only=True)

    investment_type = NestedRelatedField(meta_models.InvestmentType)
    stage = NestedRelatedField(meta_models.InvestmentProjectStage,
                               required=False)
    project_shareable = serializers.BooleanField(required=True)
    investor_company = NestedRelatedField(
        Company, required=True, allow_null=False
    )
    intermediate_company = NestedRelatedField(
        Company, required=False, allow_null=True
    )
    client_contacts = NestedRelatedField(
        Contact, many=True, required=True, allow_null=False, allow_empty=False
    )

    client_relationship_manager = NestedRelatedField(
        Advisor, required=True, allow_null=False,
        extra_fields=('first_name', 'last_name')
    )
    referral_source_adviser = NestedRelatedField(
        Advisor, required=True, allow_null=False,
        extra_fields=('first_name', 'last_name')
    )
    referral_source_activity = NestedRelatedField(
        meta_models.ReferralSourceActivity, required=True, allow_null=False
    )
    referral_source_activity_website = NestedRelatedField(
        meta_models.ReferralSourceWebsite, required=False, allow_null=True
    )
    referral_source_activity_marketing = NestedRelatedField(
        meta_models.ReferralSourceMarketing, required=False, allow_null=True
    )
    fdi_type = NestedRelatedField(
        meta_models.FDIType, required=False, allow_null=True
    )
    non_fdi_type = NestedRelatedField(
        meta_models.NonFDIType, required=False, allow_null=True
    )
    sector = NestedRelatedField(
        meta_models.Sector, required=True, allow_null=False
    )
    business_activities = NestedRelatedField(
        meta_models.InvestmentBusinessActivity, many=True, required=True,
        allow_null=False, allow_empty=False
    )
    archived_by = NestedRelatedField(
        Advisor, read_only=True, extra_fields=('first_name', 'last_name')
    )

    def validate(self, data):
        """Validates the object after individual fields have been validated.

        Performs stage-dependent validation of the different sections.
        """
        errors = validate(self.instance, data)

        if errors:
            raise serializers.ValidationError(errors)
        return data

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'id',
            'name',
            'project_code',
            'description',
            'nda_signed',
            'estimated_land_date',
            'actual_land_date',
            'project_shareable',
            'not_shareable_reason',
            'approved_commitment_to_invest',
            'approved_fdi',
            'approved_good_value',
            'approved_high_value',
            'approved_landed',
            'approved_non_fdi',
            'investment_type',
            'stage',
            'investor_company',
            'intermediate_company',
            'client_contacts',
            'client_relationship_manager',
            'referral_source_adviser',
            'referral_source_activity',
            'referral_source_activity_website',
            'referral_source_activity_marketing',
            'referral_source_activity_event',
            'fdi_type',
            'non_fdi_type',
            'sector',
            'business_activities',
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
            'nda_signed': {'required': True},
            'archived': {'read_only': True},
            'archived_on': {'read_only': True},
            'archived_reason': {'read_only': True}
        }


class IProjectAuditSerializer(serializers.Serializer):
    """Serializer for Investment Project audit log."""

    def to_representation(self, instance):
        """Overwrite serialization process completely to get the Versions."""
        versions = Version.objects.get_for_object(instance)
        version_pairs = (
            (versions[n], versions[n + 1]) for n in range(len(versions) - 1)
        )

        return {
            'results': self._construct_changelog(version_pairs),
        }

    def _construct_changelog(self, version_pairs):
        changelog = []

        for v_new, v_old in version_pairs:
            version_creator = v_new.revision.user
            creator_repr = None
            if version_creator:
                creator_repr = {
                    'id': str(version_creator.pk),
                    'first_name': version_creator.first_name,
                    'last_name': version_creator.last_name,
                    'name': version_creator.name,
                    'email': version_creator.email,
                }

            changelog.append({
                'user': creator_repr,
                'timestamp': v_new.revision.date_created,
                'comment': v_new.revision.comment or '',
                'changes': self._diff_versions(
                    v_old.field_dict, v_new.field_dict
                ),
            })

        return changelog

    @staticmethod
    def _diff_versions(old_version, new_version):
        changes = {}

        for field_name, new_value in new_version.items():
            if field_name not in old_version:
                changes[field_name] = [None, new_value]
            else:
                old_value = old_version[field_name]
                if old_value != new_value:
                    changes[field_name] = [old_value, new_value]

        return changes


class IProjectValueSerializer(serializers.ModelSerializer):
    """Serialiser for investment project value objects."""

    average_salary = NestedRelatedField(
        meta_models.SalaryRange, required=False,
        allow_null=True
    )
    value_complete = serializers.SerializerMethodField()

    def get_value_complete(self, instance):
        """Whether the value fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=IProjectValueSerializer.Meta.fields, next_stage=True
        )

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'total_investment',
            'foreign_equity_investment',
            'government_assistance',
            'number_new_jobs',
            'average_salary',
            'number_safeguarded_jobs',
            'r_and_d_budget',
            'non_fdi_r_and_d_budget',
            'new_tech_to_uk',
            'export_revenue',
            'value_complete',
            'client_cannot_provide_total_investment',
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
    uk_company = NestedRelatedField(Company, required=False, allow_null=True)
    requirements_complete = serializers.SerializerMethodField()

    def get_requirements_complete(self, instance):
        """Whether the requirements fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=IProjectRequirementsSerializer.Meta.fields, next_stage=True
        )

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'client_requirements',
            'site_decided',
            'address_line_1',
            'address_line_2',
            'address_line_3',
            'address_line_postcode',
            'competitor_countries',
            'uk_region_locations',
            'strategic_drivers',
            'client_considering_other_countries',
            'uk_company',
            'requirements_complete'
        )


class IProjectTeamSerializer(serializers.ModelSerializer):
    """Serialiser for investment project team objects."""

    project_manager = NestedRelatedField(
        Advisor, required=False, allow_null=True,
        extra_fields=('first_name', 'last_name')
    )
    project_assurance_adviser = NestedRelatedField(
        Advisor, required=False, allow_null=True,
        extra_fields=('first_name', 'last_name')
    )
    project_manager_team = NestedRelatedField(
        meta_models.Team, read_only=True
    )
    project_assurance_team = NestedRelatedField(
        meta_models.Team, read_only=True
    )
    team_complete = serializers.SerializerMethodField()

    def get_team_complete(self, instance):
        """Whether the team fields required to move to the next stage are complete."""
        return not validate(
            instance=instance, fields=IProjectTeamSerializer.Meta.fields, next_stage=True
        )

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            'project_manager',
            'project_assurance_adviser',
            'project_manager_team',
            'project_assurance_team',
            'team_complete'
        )


class IProjectUnifiedSerializer(IProjectSerializer, IProjectValueSerializer,
                                IProjectRequirementsSerializer, IProjectTeamSerializer):
    """Serialiser for investment projects, used with the new unified investment endpoint."""

    class Meta:  # noqa: D101
        model = InvestmentProject
        fields = (
            IProjectSerializer.Meta.fields +
            IProjectValueSerializer.Meta.fields +
            IProjectRequirementsSerializer.Meta.fields +
            IProjectTeamSerializer.Meta.fields
        )
        extra_kwargs = IProjectSerializer.Meta.extra_kwargs


class IProjectDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Investment Project Documents."""

    project = NestedRelatedField(
        InvestmentProject,
    )

    class Meta:  # noqa: D101
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
