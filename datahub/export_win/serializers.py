from django.db import transaction

from rest_framework.serializers import (
    BooleanField,
    ModelSerializer,
)

from datahub.company.models import Company, Contact, ExportExperience
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.export_win.models import (
    AssociatedProgramme,
    Breakdown,
    BreakdownType,
    BusinessPotential,
    CustomerResponse,
    ExpectedValueRelation,
    Experience,
    HQTeamRegionOrPost,
    HVC,
    HVOProgrammes,
    MarketingSource,
    Rating,
    SupportType,
    TeamType,
    Win,
    WinAdviser,
    WinType,
    WithoutOurSupport,
)
from datahub.metadata.models import Country, Sector, UKRegion


class BreakdownSerializer(ModelSerializer):
    """Breakdown serializer."""

    type = NestedRelatedField(BreakdownType)

    class Meta:
        model = Breakdown
        fields = (
            'id',
            'type',
            'year',
            'value',
        )


class WinAdviserSerializer(ModelSerializer):
    """Win adviser serialiser."""

    adviser = NestedAdviserField()
    team_type = NestedRelatedField(TeamType)
    hq_team = NestedRelatedField(HQTeamRegionOrPost)

    class Meta:
        model = WinAdviser
        fields = (
            'id',
            'adviser',
            'team_type',
            'hq_team',
            'location',
        )


class CustomerResponseSerializer(ModelSerializer):
    """Customer response serializer."""

    our_support = NestedRelatedField(Rating)
    access_to_contacts = NestedRelatedField(Rating)
    access_to_information = NestedRelatedField(Rating)
    improved_profile = NestedRelatedField(Rating)
    gained_confidence = NestedRelatedField(Rating)
    developed_relationships = NestedRelatedField(Rating)
    overcame_problem = NestedRelatedField(Rating)
    expected_portion_without_help = NestedRelatedField(WithoutOurSupport)
    last_export = NestedRelatedField(Experience)
    marketing_source = NestedRelatedField(MarketingSource)

    class Meta:
        model = CustomerResponse
        fields = (
            'id',
            'our_support',
            'access_to_contacts',
            'access_to_information',
            'improved_profile',
            'gained_confidence',
            'developed_relationships',
            'overcame_problem',
            'involved_state_enterprise',
            'support_improved_speed',
            'expected_portion_without_help',
            'last_export',
            'has_enabled_expansion_into_new_market',
            'has_enabled_expansion_into_existing_market',
            'has_increased_exports_as_percent_of_turnover',
            'company_was_at_risk_of_not_exporting',
            'has_explicit_export_plans',
            'agree_with_win',
            'case_study_willing',
            'comments',
            'name',
            'marketing_source',
            'other_marketing_source',
        )


class WinSerializer(ModelSerializer):
    """Win serializer."""

    adviser = NestedAdviserField()
    company = NestedRelatedField(Company)
    company_contacts = NestedRelatedField(
        Contact,
        many=True,
        extra_fields=(
            'name',
            'email',
        ),
    )
    team_members = NestedAdviserField(many=True, required=False)
    customer_location = NestedRelatedField(UKRegion)
    type = NestedRelatedField(WinType)
    country = NestedRelatedField(Country)
    goods_vs_services = NestedRelatedField(ExpectedValueRelation)
    sector = NestedRelatedField(Sector)
    hvc = NestedRelatedField(HVC, required=False)
    hvo_programme = NestedRelatedField(HVOProgrammes, required=False)
    type_of_support = NestedRelatedField(SupportType, many=True)
    lead_officer = NestedAdviserField()
    team_type = NestedRelatedField(TeamType)
    hq_team = NestedRelatedField(HQTeamRegionOrPost)
    business_potential = NestedRelatedField(BusinessPotential)
    export_experience = NestedRelatedField(ExportExperience)
    associated_programme = NestedRelatedField(AssociatedProgramme, many=True)
    customer_response = CustomerResponseSerializer(read_only=True)
    advisers = WinAdviserSerializer(many=True, required=False)

    breakdowns = BreakdownSerializer(many=True)

    complete = BooleanField(read_only=True)

    class Meta:
        model = Win
        fields = (
            'id',
            'adviser',
            'advisers',
            'breakdowns',
            'company',
            'company_contacts',
            'complete',
            'customer_location',
            'business_type',
            'description',
            'name_of_customer',
            'name_of_customer_confidential',
            'name_of_export',
            'date',
            'country',
            'type',
            'total_expected_export_value',
            'total_expected_non_export_value',
            'total_expected_odi_value',
            'goods_vs_services',
            'sector',
            'is_prosperity_fund_related',
            'hvc',
            'hvo_programme',
            'has_hvo_specialist_involvement',
            'is_e_exported',
            'type_of_support',
            'associated_programme',
            'is_personally_confirmed',
            'is_line_manager_confirmed',
            'lead_officer',
            'team_type',
            'hq_team',
            'business_potential',
            'export_experience',
            'location',
            'created_on',
            'modified_on',
            'complete',
            'customer_response',
            'country',
            'type',
            'export_experience',
            'audit',
            'customer_response',
            'team_members',
        )

    def create(self, validated_data):
        """Create win and corresponding breakdowns."""
        breakdowns = validated_data.pop('breakdowns')
        advisers = validated_data.pop('advisers', [])
        company_contacts = validated_data.pop('company_contacts')
        type_of_support = validated_data.pop('type_of_support')
        associated_programme = validated_data.pop('associated_programme')
        team_members = validated_data.pop('team_members', [])
        with transaction.atomic():
            win = Win.objects.create(**validated_data)

            for breakdown in breakdowns:
                Breakdown.objects.create(win=win, **breakdown)

            for win_adviser in advisers:
                WinAdviser.objects.create(win=win, **win_adviser)

            win.company_contacts.set(company_contacts)
            win.type_of_support.set(type_of_support)
            win.associated_programme.set(associated_programme)
            win.team_members.set(team_members)
        return win
